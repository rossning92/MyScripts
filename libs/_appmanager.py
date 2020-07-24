import yaml
import shutil
from _shutil import run_elevated
import subprocess
import sys
import os
import glob

# from _script import run_script


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


def get_executable(app_name):
    with open(os.path.join(os.path.dirname(__file__), "app_list.yaml"), "r") as f:
        app_list = yaml.load(f.read(), Loader=yaml.FullLoader)

    matched_apps = [k for k, v in app_list.items() if app_name.lower() == k.lower()]

    app = {}
    if len(matched_apps) > 0:
        app_name = matched_apps[0]
        app = app_list[app_name]

    def find_executable():
        if "executable" in app:
            for exe in app["executable"]:
                match = list(glob.glob(exe))
                if len(match) > 0:
                    return match[0]

                if shutil.which(exe):
                    return exe
        else:
            if shutil.which(app_name):
                return app_name

        return None

    # Install app if not exists
    executable = find_executable()
    if executable is None:
        if sys.platform == "win32":
            pkg_name = app_name
            if "choco" in app:
                pkg_name = app["choco"]
            
            choco_install(pkg_name)

            executable = find_executable()

        elif sys.platform == "linux":
            # if "linux_install" in app:
            #     run_script(app["linux_install"])
            #     executable = find_executable()
            pass

    return executable


if __name__ == "__main__":
    # For testing
    get_executable("7z")
