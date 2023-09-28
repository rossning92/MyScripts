import argparse
import logging
import subprocess
import sys

from _menu import Menu
from _pkgmanager import install_package
from _shutil import call2, setup_logger

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
        "msys2",
        "nodejs-lts",
        "ripgrep",
        "vscode",
        "yarn",
        # "anaconda3",
        # "androidstudio",
        # "atom",
        # "cmake --version=3.10.2 --force",
        # "miniconda3",
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
        "androidstudio",
        "audacity",
        "autohotkey",
        "blender",
        "carnac",
        "crystaldiskinfo",
        "cura-new",
        "docker-desktop",
        "dupeguru",
        "epicgameslauncher",
        "geforce-experience",
        "ghostscript",
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
        "visualstudio2019community",
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
            ["[ install custom package ]", "[ uninstall package ]"]
            + [cate for cate in PKGS if cate.startswith("@")]
            + sorted(set([app for cate in PKGS.values() for app in cate]))
        )
        idx = Menu(items=pkg_list).exec()
        if idx < 0:
            sys.exit(0)

        if idx == 0:
            name = input("please input package name: ")
            install_package(name)
        elif idx == 1:
            lines = (
                subprocess.check_output(
                    ["choco", "list", "-localonly"], universal_newlines=True
                )
                .strip()
                .splitlines()
            )
            lines = lines[1:-1]
            apps = [x.split()[0] for x in lines]

            idx = Menu(items=apps).exec()
            if idx < 0:
                sys.exit(0)

            call2(["choco", "uninstall", apps[idx], "-y"])

        else:
            install_recursive(pkg_list[idx])
