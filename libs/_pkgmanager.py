import glob
import logging
import os
import shutil
import subprocess
import sys

import yaml
from _shutil import (
    check_output,
    is_in_termux,
    refresh_env_vars,
    run_elevated,
    start_process,
)

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


def find_executable(pkg, install=False):
    # If pkg is an executable and exists
    exe_path = shutil.which(pkg)
    if exe_path:
        return exe_path

    exec = []
    if pkg in packages:
        if "exec" in packages[pkg]:
            exec = packages[pkg]["exec"]

    for p in exec:
        p = os.path.expandvars(p)
        match = list(glob.glob(p))
        if len(match) > 0:
            return match[0]

        exe_path = shutil.which(p)
        if exe_path:
            return exe_path

    if install and exec is None:
        install_package(pkg)
        return find_executable(pkg)

    return None


def require_package(pkg):
    logging.info(f"{require_package.__name__}(): {pkg}")
    # Check if pkg is an executable and exists already
    exec = find_executable(pkg)

    if exec is None:
        install_package(pkg)


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

    if sys.platform == "win32":
        choco_install(pkg, upgrade=upgrade)
    if sys.platform == "linux":
        if not shutil.which(pkg):
            logging.warning('Package "%s" cannot be found, installing...' % pkg)
            if is_in_termux():
                subprocess.check_call(["pkg", "install", pkg, "-y"])
            elif shutil.which("apt"):
                subprocess.check_call(["sudo", "apt", "install", pkg, "-y"])


def open_log_file(file):
    klogg = find_executable("klogg")
    if klogg:
        start_process([klogg, "--follow", file])
