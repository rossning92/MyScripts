from _term import SearchWindow
import sys
import subprocess

PKGS = {
    "other": [
        "miktex",
        "unity --version 2018.2.0",
        "unity --version 2018.2.14",
        "sketchup",
        "blender",
        "graphviz",
        "inkscape",
        "mousewithoutborders",
        "tightvnc",
        "gifcam",
        "autohotkey",
        "nsis",
        "teamviewer",
        "spacesniffer",
        "audacity",
        "putty",
        "thunderbird",
        "pandoc",
        "vmware-workstation-player",
        "sharex",
        "epicgameslauncher",
        "unity-hub",
        "golang",
        "nvidia-display-driver",
        "carnac",
        "win32diskimager",
        "docker-desktop",
        "rufus",
    ],
    "common": ["everything", "irfanview", "googlechrome"],
    "@ross": ["google-backup-and-sync"],
    "dev": [
        "conemu",
        "atom",
        "graphviz",
        "anaconda3",
        "miniconda3",
        # 'pycharm-community',
        "cmake",
        "cmake --version=3.10.2 --force",
        "visualstudio2017community",
        "androidstudio",
        "android-sdk",
        "llvm",
        "ripgrep",
        "vscode",
        "visualstudiocode-insiders --pre",
        "sumatrapdf",
        "nodejs",
        "microsoft-windows-terminal",
    ],
    "media": ["ffmpeg", "vlc", "imagemagick.app",],
    "for_work": ["p4v", "selenium-chrome-driver",],
    "ue4": ["directx",],
}

pkg_list = [cate for cate in PKGS if cate.startswith("@")] + sorted(
    set([app for cate in PKGS.values() for app in cate])
)
idx = SearchWindow(items=pkg_list).get_selected_index()
if idx < 0:
    sys.exit(1)

subprocess.call(
    'choco source add --name=chocolatey --priority=-1 -s="https://chocolatey.org/api/v2/"'
)

if pkg_list[idx] == "@for work":
    for pkg in PKGS["for_work"] + PKGS["media"] + PKGS["dev"] + PKGS["common"]:
        subprocess.call("choco install %s -y" % pkg)

elif pkg_list[idx].startswith("@"):
    for pkg in PKGS[pkg_list[idx]]:
        subprocess.call("choco install %s -y" % pkg)

else:
    subprocess.call("choco install %s -y" % pkg_list[idx])
