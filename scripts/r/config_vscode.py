import json
import os
import sys

from _shutil import call_echo, cd, download, gettempdir, prepend_to_path, print2, unzip

DATA_DIR = "%APPDATA%/Code"
if r"{{DATA_DIR}}":
    DATA_DIR = r"{{DATA_DIR}}"


def install_glslang():
    assert sys.platform == "win32"
    path = os.path.abspath("/tools/glslang")
    if not os.path.exists(path):
        cd(gettempdir())
        f = download(
            "https://github.com/KhronosGroup/glslang/releases/download/master-tot/glslang-master-windows-x64-Release.zip"
        )
        unzip(f, to=path)
    return os.path.abspath("/tools/glslang/bin/glslangValidator.exe")


if __name__ == "__main__":
    call_echo([sys.executable, "-m", "pip", "install", "pylint"])
    call_echo([sys.executable, "-m", "pip", "install", "autopep8"])

    print2("Update key bindings...")
    with open(os.path.expandvars(DATA_DIR + "/User/keybindings.json"), "w") as f:
        json.dump(
            [
                {
                    "key": "ctrl+shift+v",
                    "command": "markdown.showPreviewToSide",
                    "when": "!notebookEditorFocused && editorLangId == 'markdown'",
                },
                {"key": "shift+alt+r", "command": "revealFileInOS",},
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
    SETTING_CONFIG = os.path.expandvars(DATA_DIR + "/User/settings.json")
    try:
        with open(SETTING_CONFIG) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data["workbench.colorTheme"] = "Visual Studio Light"

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

    data["glsllint.glslangValidatorPath"] = install_glslang()

    # Markdown
    data["[markdown]"] = {"editor.defaultFormatter": "esbenp.prettier-vscode"}

    with open(SETTING_CONFIG, "w") as f:
        json.dump(data, f, indent=4)

    if not "{{SKIP_EXTENSIONS}}":
        print2("Install extensions...")
        extensions = [
            "donjayamanne.githistory",
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
            "cadenas.vscode-glsllint",
            "xaver.clang-format",
        ]

        prepend_to_path(r"C:\Program Files\Microsoft VS Code\bin")
        for ext in extensions:
            call_echo(["code", "--install-extension", "%s" % ext])
