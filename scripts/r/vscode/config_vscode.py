import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from _script import get_my_script_root
from _shutil import download, get_home_path, prepend_to_path, unzip

if sys.platform == "win32":
    prepend_to_path([r"C:\Program Files\Microsoft VS Code\bin"])


def install_glslangvalidator():
    if sys.platform == "win32":
        out = download(
            "https://github.com/KhronosGroup/glslang/releases/download/master-tot/glslang-master-windows-x64-Release.zip",
            save_to_tmp=True,
        )
        unzip(out, os.path.join(get_home_path(), "tools", "glslang"))
        os.remove(out)
        return os.path.join(
            get_home_path(), "tools", "glslang", "bin", "glslangValidator.exe"
        )


def run_command(args: List[str]):
    subprocess.check_call(
        args,
        # we need to set shell=True on Windows because the code command is a batch file.
        shell=sys.platform == "win32",
        stdout=subprocess.DEVNULL,
    )


def get_vscode_cmdline(data_dir=None):
    if not shutil.which("code"):
        raise Exception("cannot locate vscode command: code")

    args = ["code"]
    if data_dir:
        args += ["--user-data-dir", data_dir]
    return args


def install_extensions(extensions: list[str], data_dir=None):
    for extension in extensions:
        print(f'Installing extension "{extension}"')
        run_command(
            get_vscode_cmdline(data_dir=data_dir)
            + ["--install-extension", "%s" % extension],
        )


def update_settings(settings, data_dir):
    setting_config_file = os.path.abspath(data_dir + "/User/settings.json")
    try:
        with open(setting_config_file) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data.update(settings)

    with open(setting_config_file, "w") as f:
        json.dump(data, f, indent=4)


def pip_install(package: str):
    run_command([sys.executable, "-m", "pip", "install", package])


def setup_python(data_dir: str):
    pip_install("mypy")
    pip_install("ruff")
    pip_install("black")

    install_extensions(
        [
            "charliermarsh.ruff",
            "ms-python.black-formatter",
            "ms-python.mypy-type-checker",
            "ms-python.python",
            "ms-toolsai.jupyter",
            "njpwerner.autodocstring",
        ],
        data_dir=data_dir,
    )

    settings = {
        "[python]": {"editor.defaultFormatter": "ms-python.black-formatter"},
        "python.analysis.autoImportCompletions": True,
        "python.analysis.persistAllIndices": True,
        "python.analysis.typeCheckingMode": "basic",
        "python.experiments.enabled": False,
        "python.languageServer": "Pylance",
    }
    update_settings(settings, data_dir=data_dir)


def setup_gpt(data_dir: str):
    install_extensions(
        ["genieai.chatgpt-vscode"],
        data_dir=data_dir,
    )


def setup_color_theme(data_dir: str):
    install_extensions(["dracula-theme.theme-dracula"], data_dir=data_dir)
    update_settings({"workbench.colorTheme": "Dracula"}, data_dir=data_dir)


def setup_mermaid(data_dir: str):
    update_settings(
        {
            "mermaid-editor.preview.defaultMermaidConfig": str(
                Path(get_my_script_root()) / "settings" / "mermaid" / "config.json"
            )
        },
        data_dir=data_dir,
    )


def config_vscode(data_dir=None, compact=False, glslang=False):
    if not data_dir:
        if sys.platform == "win32":
            data_dir = os.path.expandvars("%APPDATA%/Code")
        elif sys.platform == "linux":
            data_dir = os.path.expanduser("~/.config/Code")
        else:
            raise Exception("OS not supported: {}".format(sys.platform))

    setup_python(data_dir=data_dir)
    setup_gpt(data_dir=data_dir)
    setup_mermaid(data_dir=data_dir)
    # setup_color_theme(data_dir=data_dir)

    install_extensions(
        [
            "mhutchie.git-graph",
            "stkb.rewrap",
            "streetsidesoftware.code-spell-checker",
            # C++
            "ms-vscode.cpptools",
            "ms-vscode.cpptools-extension-pack",
            # Markdown
            "yzhang.markdown-all-in-one",
            "mushan.vscode-paste-image",
            # Note-taking
            "foam.foam-vscode",
            # Javascript
            "dbaeumer.vscode-eslint",
            "esbenp.prettier-vscode",
            # Bash
            "foxundermoon.shell-format",
            # AutoHotkey
            "cweijan.vscode-autohotkey-plus",
            # GLSL Shader
            "circledev.glsl-canvas",  # shader preview
            # "cadenas.vscode-glsllint",
            "xaver.clang-format",
            # Powershell
            "ms-vscode.powershell",
            # Mermaid Diagram
            "bierner.markdown-mermaid",
            "tomoyukim.vscode-mermaid-editor",
            # csv
            "janisdd.vscode-edit-csv",
            # Lua
            "sumneko.lua",
        ],
        data_dir=data_dir,
    )

    print("Update key bindings...")
    with open(os.path.abspath(data_dir + "/User/keybindings.json"), "w") as f:
        json.dump(
            [
                {
                    "key": "ctrl+shift+v",
                    "command": "markdown.showPreviewToSide",
                    "when": "!notebookEditorFocused && editorLangId == 'markdown'",
                },
                {
                    "key": "ctrl+shift+v",
                    "command": "mermaid-editor.preview",
                    "when": "resourceExtname == '.mmd'",
                },
                {"key": "shift+alt+r", "command": "revealFileInOS"},
                {"key": "shift+alt+c", "command": "copyFilePath"},
                {"key": "ctrl+shift+enter", "command": "editor.action.openLink"},
                {
                    "key": "alt+l",
                    "command": "markdown.extension.editing.toggleList",
                    "when": (
                        "editorTextFocus"
                        " && !editorReadonly"
                        " && editorLangId == 'markdown'"
                    ),
                },
                {"key": "ctrl+shift+r", "command": "workbench.action.reloadWindow"},
                {"key": "ctrl+shift+alt+enter", "command": "-jupyter.runAndDebugCell"},
                {
                    "key": "alt+left",
                    "command": "workbench.action.navigateBack",
                    "when": "canNavigateBack",
                },
                {
                    "key": "alt+right",
                    "command": "workbench.action.navigateForward",
                    "when": "canNavigateForward",
                },
                {
                    "key": "shift+alt+f",
                    "command": "references-view.findReferences",
                    "when": "editorHasReferenceProvider",
                },
                {
                    "key": "shift+alt+f12",
                    "command": "-references-view.findReferences",
                    "when": "editorHasReferenceProvider",
                },
                # Genie:
                {
                    "key": "ctrl+k a",
                    "command": "chatgpt-vscode.adhoc",
                    "when": "editorHasSelection",
                },
                {
                    "key": "ctrl+k o",
                    "command": "chatgpt-vscode.optimize",
                    "when": "editorHasSelection",
                },
            ],
            f,
            indent=4,
        )

    print("Update settings...")

    settings = {
        "cSpell.enabledLanguageIds": ["markdown", "text"],
        "editor.codeActionsOnSave": {"source.organizeImports": True},
        "editor.formatOnSave": True,
        "editor.minimap.enabled": False,
        "files.trimTrailingWhitespace": True,
        "pasteImage.path": "${currentFileNameWithoutExt}",
        "search.exclude": {"**/build": True},
        "window.title": "${rootName}${separator}${appName}",
        "workbench.editor.enablePreviewFromQuickOpen": False,
    }

    if glslang and sys.platform == "win32":
        settings["glsllint.glslangValidatorPath"] = install_glslangvalidator()

    settings.update(
        {
            "[markdown]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
            "[html]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
            "[jsonc]": {"editor.defaultFormatter": "vscode.json-language-features"},
        }
    )

    if compact:
        settings.update(
            {
                "workbench.colorTheme": "One Dark Pro Flat",
                "workbench.startupEditor": "newUntitledFile",
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
            }
        )

    update_settings(settings, data_dir=data_dir)


if __name__ == "__main__":
    data_dir = os.environ.get("_DATA_DIR")
    config_vscode(data_dir=data_dir, compact=False, glslang=True)
