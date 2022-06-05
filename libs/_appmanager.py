import glob
import os
import shutil
import subprocess
import sys

import yaml

from _shutil import call_echo, run_elevated


def install_alacritty_linux():
    call_echo("sudo add-apt-repository ppa:mmstick76/alacritty -y")
    call_echo("sudo apt update")
    call_echo("sudo apt install -y alacritty")


def choco_install(name):
    out = subprocess.check_output(
        "choco list --local-only %s" % name, shell=True, universal_newlines=True
    )
    if "0 packages installed" in out:
        print("Installing %s..." % name)
        run_elevated(
            [
                "choco",
                "source",
                "add",
                "--name=chocolatey",
                "--priority=100",
                '-s="https://chocolatey.org/api/v2/"',
            ]
        )
        run_elevated(["choco", "install", "--source=chocolatey", name, "-y"])


def get_executable(name):
    with open(os.path.join(os.path.dirname(__file__), "app_list.yaml"), "r") as f:
        app_list = yaml.load(f.read(), Loader=yaml.FullLoader)

    matched_apps = [k for k, v in app_list.items() if name.lower() == k.lower()]

    app = {}
    if len(matched_apps) > 0:
        name = matched_apps[0]
        app = app_list[name]

    def find_executable():
        if "executable" in app:
            for exec_path in app["executable"]:
                exec_path = os.path.expandvars(exec_path)
                match = list(glob.glob(exec_path))
                if len(match) > 0:
                    return match[0]

                if shutil.which(exec_path):
                    return exec_path
        else:
            if shutil.which(name):
                return name

        return None

    # Install app if not exists
    executable = find_executable()
    if executable is None:
        print("WARN: %s not found, installing..." % name)
        if sys.platform == "win32":
            pkg_name = name
            if "choco" in app:
                pkg_name = app["choco"]

            choco_install(pkg_name)

            executable = find_executable()

        elif sys.platform == "linux":
            if "alacritty" == name:
                install_alacritty_linux()

    return executable
