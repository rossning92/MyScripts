from _shutil import *
import json

DATA_DIR = "%APPDATA%/Code"
if r"{{DATA_DIR}}":
    DATA_DIR = r"{{DATA_DIR}}"


def install_glslang():
    assert sys.platform == "win32"
    path = os.path.abspath("/tools/glslang")
    if not exists(path):
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
    with open(expandvars(DATA_DIR + "/User/keybindings.json"), "w") as f:
        json.dump(
            [
                {
                    "key": "ctrl+shift+v",
                    "command": "markdown-preview-enhanced.openPreviewToTheSide",
                    "when": "editorLangId == 'markdown'",
                },
                {"key": "shift+alt+r", "command": "revealFileInOS",},
                {"key": "shift+alt+c", "command": "copyFilePath"},
                {"key": "ctrl+alt+enter", "command": "editor.action.openLink"},
            ],
            f,
            indent=4,
        )

    print2("Update settings...")
    f = expandvars(DATA_DIR + "/User/settings.json")
    try:
        data = json.load(open(f))
    except FileNotFoundError:
        data = {}

    data["workbench.colorTheme"] = "Visual Studio Light"
    data["python.pythonPath"] = sys.executable.replace("\\", "/")
    data["cSpell.enabledLanguageIds"] = ["markdown", "text"]
    data["search.exclude"] = {"**/build": True}
    data["pasteImage.path"] = "${currentFileNameWithoutExt}"
    data["workbench.editor.enablePreviewFromQuickOpen"] = False

    call_echo([sys.executable, "-m", "pip", "install", "black"])
    data["python.formatting.provider"] = "black"

    data["glsllint.glslangValidatorPath"] = install_glslang()

    json.dump(data, open(f, "w"), indent=4)

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
            # JS
            "esbenp.prettier-vscode",
            # Shell script
            "foxundermoon.shell-format",
            # Python
            "njpwerner.autodocstring",
            # "ms-vscode-remote.vscode-remote-extensionpack",
            # Ahk
            "cweijan.vscode-autohotkey-plus",
            # Shader
            "slevesque.shader",
            "cadenas.vscode-glsllint",
            "xaver.clang-format",
        ]

        prepend_to_path(r"C:\Program Files\Microsoft VS Code\bin")
        for ext in extensions:
            call_echo("code --install-extension %s" % ext)
