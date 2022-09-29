import argparse
import logging
import sys

from _pkgmanager import install_package
from _shutil import setup_logger
from _term import Menu

PKGS = {
    "@common": [
        "alacritty",
        "everything",
        "git-lfs",
        "git",
        "googlechrome",
        "googledrive",
        "irfanview",
        "mpv",
        "sharex",
        "sumatrapdf",
        "tightvnc",
        "vnc-viewer",
    ],
    "@ross": [
        "@common",
        "@dev",
    ],
    "@dev": [
        "7zip",
        "android-sdk",
        "chromium",
        "cmake",
        "conemu",
        "ffmpeg",
        "graphviz",
        "hxd",
        "imagemagick.app",
        "llvm",
        "nodejs-lts",
        "ripgrep",
        "vscode",
        "yarn",
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
        "jcpicker",
        "microsoft-windows-terminal",
        "miktex",
        "mongodb",
        "mousewithoutborders",
        "nsis",
        "nvidia-display-driver",
        "ocenaudio",
        "ontopreplica",
        "pandoc",
        "putty",
        "renamer",
        "rufus",
        "scrcpy",
        "shotcut",
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


def install_recursive(name):
    logging.info('install_recursive(name="%s")' % name)
    if name.startswith("@"):
        for pkg in PKGS[name]:
            install_recursive(pkg)

    else:
        install_package(name)


if __name__ == "__main__":
    setup_logger()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", help="package name", type=str, default=None)
    args = parser.parse_args()

    if args.name:
        install_recursive(args.name)

    else:
        pkg_list = (
            ["input package name"]
            + [cate for cate in PKGS if cate.startswith("@")]
            + sorted(set([app for cate in PKGS.values() for app in cate]))
        )
        idx = Menu(items=pkg_list).exec()
        if idx < 0:
            sys.exit(0)

        if idx == 0:
            name = input("please input package name: ")
            install_package(name)
        else:
            install_recursive(pkg_list[idx])
