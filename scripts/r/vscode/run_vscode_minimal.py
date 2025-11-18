import os
import sys

from utils.process import start_process
from vscode.config_vscode import (
    setup_color_theme,
    update_settings,
    update_settings_common,
)


def _main():
    if sys.platform == "win32":
        os.environ["PATH"] = (
            os.environ["PATH"] + os.pathsep + r"C:\Program Files\Microsoft VS Code"
        )

    data_dir = os.path.expanduser("~/VSCodeMinimalUserData")

    setup_color_theme(data_dir=data_dir)

    update_settings_common()

    update_settings(
        settings={
            "explorer.openEditors.visible": 0,
            "workbench.activityBar.visible": False,
            "workbench.statusBar.visible": False,
            "window.zoomLevel": 0,
            "window.menuBarVisibility": "compact",
            "extensions.ignoreRecommendations": True,
            "liveServer.settings.AdvanceCustomBrowserCmdLine": "chrome --new-window",
            "extensions.autoCheckUpdates": False,
            "update.mode": "manual",
            # Terminal
            "terminal.integrated.profiles.windows": {
                "Command Prompt": {"path": "cmd", "args": ["/k"]}
            },
            "terminal.integrated.defaultProfile.windows": "Command Prompt",
            "scm.diffDecorations": "none",
        },
        data_dir=data_dir,
    )

    args = ["code", "--user-data-dir", data_dir]
    if os.environ.get("PROJECT_DIR"):
        args.append(os.environ["PROJECT_DIR"])
    start_process(args)


if __name__ == "__main__":
    _main()
