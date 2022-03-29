import glob
import json
import os
import subprocess
import sys
import tempfile

from _shutil import call_echo, cd, download, prepend_to_path, print2, unzip


def get_vscode_cmdline(data_dir=None):
    args = ["code"]
    if data_dir is not None:
        extensions_dir = os.path.join(data_dir, "extensions")
        args += [
            "--user-data-dir",
            data_dir,
            "--extensions-dir",
            extensions_dir,
        ]
    return args


def install_glslang():
    assert sys.platform == "win32"
    path = os.path.abspath("/tools/glslang")
    if not os.path.exists(path):
        cd(tempfile.gettempdir())
        f = download(
            "https://github.com/KhronosGroup/glslang/releases/download/master-tot/glslang-master-windows-x64-Release.zip"
        )
        unzip(f, to=path)
    return os.path.abspath("/tools/glslang/bin/glslangValidator.exe")


def install_extensions(data_dir=None):
    print2("Install extensions...")
    extensions = [
        # "donjayamanne.githistory",
        "ms-python.python",
        "ms-vscode.cpptools",
        "stkb.rewrap",
        "streetsidesoftware.code-spell-checker",
        # Markdown
        # "shd101wyy.markdown-preview-enhanced",
        # "mdickin.markdown-shortcuts",
        "yzhang.markdown-all-in-one",
        "mushan.vscode-paste-image",
        # JS
        "esbenp.prettier-vscode",
        # Shell script
        "foxundermoon.shell-format",
        # Python
        "njpwerner.autodocstring",
        # "ms-vscode-remote.vscode-remote-extensionpack",
        "ms-toolsai.jupyter",
        # Ahk
        "cweijan.vscode-autohotkey-plus",
        # Shader
        "slevesque.shader",
        # "cadenas.vscode-glsllint",
        "xaver.clang-format",
    ]

    prepend_to_path(r"C:\Program Files\Microsoft VS Code\bin")
    for extension in extensions:
        call_echo(
            get_vscode_cmdline(data_dir=data_dir)
            + ["--install-extension", "%s" % extension]
        )


def config_vscode(data_dir=None, compact=False, glslang=False):
    # call_echo([sys.executable, "-m", "pip", "install", "pylint"])
    # call_echo([sys.executable, "-m", "pip", "install", "autopep8"])
    call_echo([sys.executable, "-m", "pip", "install", "mypy"])

    install_extensions(data_dir=data_dir)

    if data_dir is None:
        data_dir = os.path.expandvars("%APPDATA%/Code")

    print2("Update key bindings...")
    with open(os.path.abspath(data_dir + "/User/keybindings.json"), "w") as f:
        json.dump(
            [
                {
                    "key": "ctrl+shift+v",
                    "command": "markdown.showPreviewToSide",
                    "when": "!notebookEditorFocused && editorLangId == 'markdown'",
                },
                {"key": "shift+alt+r", "command": "revealFileInOS"},
                {"key": "shift+alt+c", "command": "copyFilePath"},
                {"key": "ctrl+shift+enter", "command": "editor.action.openLink"},
                {
                    "key": "alt+l",
                    "command": "markdown.extension.editing.toggleList",
                    "when": "editorTextFocus && !editorReadonly && editorLangId == 'markdown'",
                },
                {"key": "ctrl+shift+r", "command": "workbench.action.reloadWindow"},
                {"key": "ctrl+shift+alt+enter", "command": "-jupyter.runAndDebugCell"},
            ],
            f,
            indent=4,
        )

    print2("Update settings...")
    SETTING_CONFIG = os.path.abspath(data_dir + "/User/settings.json")
    try:
        with open(SETTING_CONFIG) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data["workbench.colorTheme"] = "Default Light+"

    data["cSpell.enabledLanguageIds"] = ["markdown", "text"]
    data["search.exclude"] = {"**/build": True}
    data["pasteImage.path"] = "${currentFileNameWithoutExt}"
    data["workbench.editor.enablePreviewFromQuickOpen"] = False
    data["grammarly.autoActivate"] = False

    # Python
    call_echo([sys.executable, "-m", "pip", "install", "black"])
    data["python.pythonPath"] = sys.executable.replace("\\", "/")
    data["python.formatting.provider"] = "black"
    # Workaround for "has no member" issues
    data["python.linting.pylintArgs"] = [
        "--errors-only",
        "--generated-members=numpy.* ,torch.* ,cv2.* , cv.*",
    ]
    data["python.linting.mypyEnabled"] = True
    data["python.linting.enabled"] = True
    data["python.linting.pylintEnabled"] = False
    data["python.languageServer"] = "Pylance"
    data["window.title"] = "${rootName}${separator}${activeEditorShort}"

    if glslang and sys.platform == "win32":
        data["glsllint.glslangValidatorPath"] = install_glslang()

    data.update(
        {
            "[markdown]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
            "[html]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
            "[jsonc]": {"editor.defaultFormatter": "vscode.json-language-features"},
        }
    )

    if compact:
        data.update(
            {
                "workbench.colorTheme": "One Dark Pro Flat",
                "workbench.startupEditor": "newUntitledFile",
                "editor.minimap.enabled": False,
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

    with open(SETTING_CONFIG, "w") as f:
        json.dump(data, f, indent=4)

    subprocess.Popen(get_vscode_cmdline(data_dir=data_dir), shell=True, close_fds=True)


if __name__ == "__main__":
    data_dir = r"{{_DATA_DIR}}" if r"{{_DATA_DIR}}" else None
    config_vscode(data_dir=data_dir, compact=False)
