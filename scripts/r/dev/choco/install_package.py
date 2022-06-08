import sys

from _shutil import call_echo, proc_lines
from _term import Menu

PKGS = {
    "@common": [
        "alacritty",
        "everything",
        "git",
        "googlechrome",
        "irfanview",
        "mpv",
        "sumatrapdf",
        "tightvnc",
    ],
    "@ross": ["google-backup-and-sync"],
    "@dev": [
        "7zip",
        "android-sdk",
        "chromium",
        "cmake",
        "conemu",
        "ffmpeg",
        "graphviz",
        "imagemagick.app",
        "llvm",
        "microsoft-windows-terminal",
        "nodejs",
        "ripgrep",
        "vscode",
        # "anaconda3",
        # "androidstudio",
        # "atom",
        # "cmake --version=3.10.2 --force",
        # "miniconda3",
        # "pycharm-community",
        # "visualstudio2017community",
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
        "carnac",
        "cura-new",
        "docker-desktop",
        "epicgameslauncher",
        "geforce-experience",
        "gifcam",
        "gimp",
        "golang",
        "graphviz",
        "inkscape",
        "miktex",
        "mongodb",
        "mousewithoutborders",
        "nsis",
        "nvidia-display-driver",
        "ontopreplica",
        "pandoc",
        "putty",
        "renamer",
        "rufus",
        "scrcpy",
        "sharex",
        "sketchup",
        "spacesniffer",
        "teamviewer",
        "thunderbird",
        "tightvnc",
        "treesizefree",
        "unity-hub",
        "vmware-workstation-player",
        "win32diskimager",
    ],
}


def install_package(name):
    # choco list -lo
    lines = proc_lines(["choco", "list", "-lo"])
    lines = [x for x in lines if x.startswith(name)]

    if len(lines) > 0:
        print("Upgrade `%s`..." % name)
        call_echo(
            ["choco", "upgrade", name, "-y", "-s", "https://chocolatey.org/api/v2/"],
            check=False,
        )
    else:
        print("Install `%s`..." % name)
        call_echo(
            ["choco", "install", name, "-y", "-s", "https://chocolatey.org/api/v2/"],
            check=False,
        )


if __name__ == "__main__":
    pkg_list = [cate for cate in PKGS if cate.startswith("@")] + sorted(
        set([app for cate in PKGS.values() for app in cate])
    )
    idx = Menu(items=pkg_list).exec()
    if idx < 0:
        sys.exit(1)

    if pkg_list[idx].startswith("@"):
        for pkg in PKGS[pkg_list[idx]]:
            install_package(pkg)

    else:
        install_package(pkg_list[idx])
