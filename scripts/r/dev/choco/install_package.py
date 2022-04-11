import sys

from _shutil import call_echo, proc_lines
from _term import Menu
from _script import run_script

PKGS = {
    "@common": [
        "everything",
        "irfanview",
        "googlechrome",
        "mpv",
        "sumatrapdf",
        "tightvnc",
        "git",
    ],
    "@ross": ["google-backup-and-sync"],
    "@dev": [
        "7zip",
        "android-sdk",
        "androidstudio",
        "atom",
        "cmake --version=3.10.2 --force",
        "cmake",
        "conemu",
        "ffmpeg",
        "graphviz",
        "imagemagick.app",
        "llvm",
        "microsoft-windows-terminal",
        "nodejs",
        "ripgrep",
        "visualstudio2017community",
        "vscode",
        "vscode",
        # "anaconda3",
        # "miniconda3",
        # "pycharm-community",
        # "visualstudiocode-insiders --pre",
    ],
    "@gamedev": [
        "renderdoc",
    ],
    "@media": ["ffmpeg", "imagemagick.app", "shotcut"],
    "@work": [
        "p4v",
        "selenium-chrome-driver",
    ],
    "@ue4": [
        "directx",
    ],
    "@other": [
        "audacity",
        "autohotkey",
        "blender",
        "renamer",
        "carnac",
        "docker-desktop",
        "epicgameslauncher",
        "geforce-experience",
        "gifcam",
        "golang",
        "graphviz",
        "inkscape",
        "miktex",
        "mousewithoutborders",
        "nsis",
        "nvidia-display-driver",
        "pandoc",
        "putty",
        "rufus",
        "scrcpy",
        "sharex",
        "sketchup",
        "spacesniffer",
        "teamviewer",
        "thunderbird",
        "tightvnc",
        "unity-hub",
        "vmware-workstation-player",
        "win32diskimager",
        "mongodb",
        "golang",
        "ontopreplica",
        "docker-desktop",
        "gimp",
        "cura-new",
        "treesizefree",
    ],
}


def install_package(name):
    # choco list -lo
    lines = proc_lines(["choco", "list", "-lo"])
    lines = [x for x in lines if x.startswith(name)]

    if len(lines) > 0:
        print("Upgrade `%s`..." % name)
        call_echo(["choco", "upgrade", name, "-y"])
    else:
        print("Install `%s`..." % name)
        call_echo(["choco", "install", name, "-y"])


if __name__ == "__main__":
    run_script("add_default_source")

    pkg_list = [cate for cate in PKGS if cate.startswith("@")] + sorted(
        set([app for cate in PKGS.values() for app in cate])
    )
    idx = Menu(items=pkg_list).exec()
    if idx < 0:
        sys.exit(1)

    call_echo(
        [
            "choco",
            "source",
            "add",
            "--name=chocolatey",
            "--priority=-1",
            '-s="https://chocolatey.org/api/v2/"',
        ]
    )

    if pkg_list[idx].startswith("@"):
        for pkg in PKGS[pkg_list[idx]]:
            install_package(pkg)

    else:
        install_package(pkg_list[idx])
