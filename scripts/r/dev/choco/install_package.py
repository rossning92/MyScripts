from _term import Menu
import sys
import subprocess

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
        "conemu",
        "atom",
        "graphviz",
        # "anaconda3",
        # "miniconda3",
        # "pycharm-community",
        "cmake",
        "cmake --version=3.10.2 --force",
        "visualstudio2017community",
        "androidstudio",
        "android-sdk",
        "llvm",
        "ripgrep",
        "vscode",
        # "visualstudiocode-insiders --pre",
        "nodejs",
        "microsoft-windows-terminal",
        "vscode",
        "ffmpeg",
        "imagemagick.app",
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
        "bulkrenameutility",
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
    ],
}

pkg_list = [cate for cate in PKGS if cate.startswith("@")] + sorted(
    set([app for cate in PKGS.values() for app in cate])
)
idx = Menu(items=pkg_list).get_selected_index()
if idx < 0:
    sys.exit(1)

subprocess.call(
    'choco source add --name=chocolatey --priority=-1 -s="https://chocolatey.org/api/v2/"'
)


if pkg_list[idx].startswith("@"):
    for pkg in PKGS[pkg_list[idx]]:
        subprocess.call("choco install %s -y" % pkg)

else:
    subprocess.call("choco install %s -y" % pkg_list[idx])
