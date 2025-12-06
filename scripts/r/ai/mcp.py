import json
import subprocess
from typing import Any, Dict, List, Optional, Sequence, cast

from ai.tool_use import ToolDefinition, ToolParam, ToolUse
from utils.jsonschema import JSONSchema


# Spec: https://modelcontextprotocol.io/specification/2025-06-18/basic
class MCPClient:
    def __init__(self, command: Sequence[str]) -> None:
        self.__command = list(command)
        self.__proc: Optional[subprocess.Popen[str]] = None
        self.__next_id = 0

    def _ensure_process(self) -> None:
        if self.__proc is None:
            self.__proc = subprocess.Popen(
                self.__command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.__next_id = 0

    def _send(self, payload: Dict[str, Any]) -> None:
        if self.__proc is None or self.__proc.stdin is None:
            raise RuntimeError("MCP process not started")
        message = json.dumps(payload)
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
        return json.loads(line)

    def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> int:
        self.__next_id += 1
        request_id = self.__next_id
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        return request_id

    def _send_notification(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def _wait_for_result(self, request_id: int) -> Dict[str, Any]:
        while True:
            message = self._read_message()
            if "id" not in message:
                continue
            if message["id"] != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"MCP request failed: {message['error']}")
            result = message.get("result")
            if not isinstance(result, dict):
                return {}
            return result

    def initialize(self) -> None:
        self._ensure_process()

        init_id = self._send_request(
            "initialize",
            {
                "protocolVersion": "1.0",
                "clientInfo": {"name": "MyScripts-MCP", "version": "1.0"},
                "capabilities": {},
            },
        )
        self._wait_for_result(init_id)
        self._send_notification("initialized", {})

    def list_tools(self) -> List[ToolDefinition]:
        self._ensure_process()

        list_id = self._send_request("tools/list", {})
        result = self._wait_for_result(list_id)

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

        if self.__proc.stdin:
            self.__proc.stdin.close()

        try:
            self.__proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.__proc.terminate()  # sends SIGTERM
            try:
                self.__proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.__proc.kill()  # send SIGKILL
                self.__proc.wait()

    def call_tool(self, tool: ToolUse) -> Optional[str]:
        self._ensure_process()

        request_id = self._send_request(
            "tools/call",
            {
                "name": tool["tool_name"],
                "arguments": tool.get("args", {}),
            },
        )
        result = self._wait_for_result(request_id)

        content = result["content"]
        assert isinstance(content, list)
        for item in content:
            assert isinstance(item, dict)
            if item["type"] == "text":
                return item["text"]

        return None
