import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Sequence, cast

from ai.tool_use import ToolDefinition, ToolParam, ToolUse
from utils.jsonschema import JSONSchema

_logger = logging.getLogger(__name__)


# Spec: https://modelcontextprotocol.io/specification/2025-06-18/basic
class MCPClient:
    def __init__(self, command: Sequence[str]) -> None:
        self.__command = list(command)
        self.__proc: Optional[subprocess.Popen[str]] = None
        self.__next_id = 0

    def _ensure_process(self) -> None:
        if self.__proc is None:
            _logger.debug("Starting MCP process: %s", self.__command)
            self.__proc = subprocess.Popen(
                self.__command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            self.__next_id = 0

    def _send(self, payload: Dict[str, Any]) -> None:
        if self.__proc is None or self.__proc.stdin is None:
            raise RuntimeError("MCP process not started")
        message = json.dumps(payload)
        _logger.debug("MCP send: %s", message)
        self.__proc.stdin.write(message + "\n")
        self.__proc.stdin.flush()

    def _read_message(self) -> Dict[str, Any]:
        if self.__proc is None or self.__proc.stdout is None:
            raise RuntimeError("MCP process not started")
        line = self.__proc.stdout.readline()
        if line == "":
            stderr_snapshot = (
                self.__proc.stderr.read() if self.__proc and self.__proc.stderr else ""
            )
            raise RuntimeError(
                f"Unexpected EOF while reading MCP response. Stderr: {stderr_snapshot}"
            )
        _logger.debug("MCP recv: %s", line.rstrip("\n"))
        return json.loads(line)

    def _request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self.__next_id += 1
        request_id = self.__next_id
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        _logger.debug("MCP request id=%s method=%s", request_id, method)
        self._send(payload)

        message = self._read_message()
        if message.get("jsonrpc") != "2.0":
            raise RuntimeError(
                f"Invalid MCP response: jsonrpc must be '2.0' (got {message.get('jsonrpc')!r})"
            )

        if message.get("id") != request_id:
            raise RuntimeError(
                f"Received response for unexpected id: {message.get('id')} (expected {request_id})"
            )

        has_result = "result" in message
        has_error = "error" in message
        if has_result and has_error:
            raise RuntimeError(
                "Invalid MCP response: both 'result' and 'error' are set"
            )
        if not has_result and not has_error:
            raise RuntimeError(
                "Invalid MCP response: neither 'result' nor 'error' is set"
            )

        if has_error:
            err = message["error"]
            if not isinstance(err, dict):
                raise RuntimeError(f"Invalid MCP error object: {err!r}")
            code = err["code"]
            err_message = err["message"]
            if not isinstance(code, int) or not isinstance(err_message, str):
                raise RuntimeError(f"Invalid MCP error object: {err!r}")
            _logger.debug("MCP error for id=%s: %s", request_id, err)
            raise RuntimeError(f"MCP request failed ({code}): {err_message}")

        return message.get("result")

    def _send_notification(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def initialize(self) -> None:
        self._ensure_process()

        self._request(
            "initialize",
            {
                "protocolVersion": "1.0",
                "clientInfo": {"name": "MyScripts-MCP", "version": "1.0"},
                "capabilities": {},
            },
        )
        self._send_notification("initialized", {})

    def list_tools(self) -> List[ToolDefinition]:
        self._ensure_process()

        result = self._request("tools/list", {})

        tool_definitions: List[ToolDefinition] = []
        for tool in result["tools"]:
            if not isinstance(tool, dict):
                continue
            params: List[ToolParam] = []
            for param_name, param_schema in tool["inputSchema"]["properties"].items():
                assert isinstance(param_schema, dict)
                params.append(
                    ToolParam(
                        name=param_name,
                        type=cast(JSONSchema, param_schema),
                        description=param_schema["description"],
                    )
                )
            tool_definitions.append(
                ToolDefinition(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=params,
                    required=tool["inputSchema"].get("required", []),
                )
            )
        return tool_definitions

    def close(self) -> None:
        if self.__proc is None:
            return

        _logger.debug("Closing MCP process")

        if self.__proc.stdin:
            self.__proc.stdin.close()

        try:
            self.__proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _logger.debug("MCP process did not exit; terminating")
            self.__proc.terminate()  # sends SIGTERM
            try:
                self.__proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _logger.debug("MCP process did not terminate; killing")
                self.__proc.kill()  # send SIGKILL
                self.__proc.wait()

    def call_tool(self, tool: ToolUse) -> Optional[str]:
        self._ensure_process()

        result = self._request(
            "tools/call",
            {
                "name": tool["tool_name"],
                "arguments": tool.get("args", {}),
            },
        )

        content = result["content"]  # unstructured content
        assert isinstance(content, list)
        for item in content:
            assert isinstance(item, dict)
            if item["type"] == "text":
                return item["text"]

        return None
