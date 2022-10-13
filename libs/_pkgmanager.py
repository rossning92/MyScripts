import glob
import logging
import os
import shutil
import subprocess

import yaml

from _shutil import check_output, refresh_env_vars, run_elevated

with open(
    os.path.abspath(
        os.path.dirname(os.path.abspath(__file__)) + "/../settings/packages.yml"
    ),
    "r",
) as f:
    packages = yaml.load(f.read(), Loader=yaml.FullLoader)


def install_alacritty_linux():
    run_elevated("sudo add-apt-repository ppa:mmstick76/alacritty -y")
    run_elevated("sudo apt update")
    run_elevated("sudo apt install -y alacritty")


def find_executable(pkg):
    exec = []
    if pkg in packages:
        if "exec" in packages[pkg]:
            exec = packages[pkg]["exec"]

    for p in exec:
        p = os.path.expandvars(p)
        match = list(glob.glob(p))
        if len(match) > 0:
            return match[0]

        if shutil.which(p):
            return p

    if shutil.which(pkg):
        return pkg

    return None


def require_package(pkg):
    exec = find_executable(pkg)
    if exec is None:
        install_package(pkg)
    return find_executable(pkg)


def choco_install(pkg, upgrade=False):
    if pkg in packages:
        if "choco" in packages[pkg]:
            pkg = packages[pkg]["choco"]

    out = check_output(["choco", "list", "--local", "--exact", pkg])

    if "0 packages installed" in out:
        logging.info("Install `%s`..." % pkg)
        run_elevated(
            ["choco", "install", pkg, "-y", "-s", "https://chocolatey.org/api/v2/"],
        )

    elif upgrade:
        logging.info("Upgrade `%s`..." % pkg)
        run_elevated(
            ["choco", "upgrade", pkg, "-y", "-s", "https://chocolatey.org/api/v2/"],
        )

    refresh_env_vars()


def install_package(pkg, upgrade=False):
    if pkg == "lux":
        require_package("golang")
        subprocess.check_call(["go", "install", "github.com/iawia002/lux@latest"])
        return

    choco_install(pkg, upgrade=upgrade)
