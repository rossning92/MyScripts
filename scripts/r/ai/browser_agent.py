import os

from ai.agent_menu import AgentMenu

_PLAYWRIGHT_MCP_COMMAND = "npx --yes @playwright/mcp@latest"


class BrowserAgent(AgentMenu):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(
            data_dir=os.path.join(".config", "browser_agent"),
            mcp=[{"command": _PLAYWRIGHT_MCP_COMMAND}],
            model="claude-sonnet-4-5",
            **kwargs,
        )


def _main():
    menu = BrowserAgent()
    menu.exec()


if __name__ == "__main__":
    _main()
