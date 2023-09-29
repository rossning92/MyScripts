import glob
import logging
import os
import shutil
import subprocess
import sys

from _shutil import (
    check_output,
    get_home_path,
    is_in_termux,
    load_json,
    refresh_env_vars,
    run_elevated,
    start_process,
)

packages = load_json(
    os.path.abspath(
        os.path.dirname(os.path.abspath(__file__)) + "/../settings/packages.json"
    )
)


def find_executable(pkg, install=False):
    # If pkg is an executable and exists
    exe_path = shutil.which(pkg)
    if exe_path:
        return exe_path

    executables = []
    if pkg in packages:
        if "executables" in packages[pkg]:
            executables = packages[pkg]["executables"]

    for executable in executables:
        executable = os.path.expandvars(executable)
        match = list(glob.glob(executable))
        if len(match) > 0:
            return match[0]

        exe_path = shutil.which(executable)
        if exe_path:
            return exe_path

    if install and executables is None:
        require_package(pkg)
        return find_executable(pkg)

    return None


def require_package(pkg, wsl=False):
    if "dependantPackages" in packages:
        for pkg in packages["dependantPackages"]:
            require_package(pkg)

    if pkg in packages:
        if "golang" in packages[pkg]:
            require_package("golang")
            if "packagePath" in packages[pkg]["golang"]:
                go_pkg_path = packages[pkg]["golang"]["packagePath"]
                if not _is_go_package_installed(go_pkg_path):
                    logging.info(f"Installing go package: {go_pkg_path}...")
                    subprocess.check_call(["go", "install", go_pkg_path])
                return

        elif "pacman" in packages[pkg] and shutil.which("pacman"):
            pacmanPackage = packages[pkg]["pacman"]["packageName"]
            if (
                subprocess.call(
                    ["pacman", "-Q", pacmanPackage],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
                != 0
            ):
                logging.info(f"Installing package using pacman: {pkg}...")
                print(["sudo", "pacman", "-S", pacmanPackage])
                subprocess.check_call(
                    ["sudo", "pacman", "-Sy", "--noconfirm", pacmanPackage]
                )
            return

        elif "termux" in packages[pkg] and is_in_termux():
            if (
                subprocess.call(
                    ["dpkg", "-s", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
                != 0
            ):
                logging.warning(f'Package "{pkg}" was not found, installing...')
                subprocess.check_call(["pkg", "install", pkg, "-y"])
            return

        elif wsl and sys.platform == "win32":
            if (
                subprocess.call(
                    ["wsl", "dpkg", "-s", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
                != 0
            ):
                logging.warning(f'Package "{pkg}" was not found, installing...')
                subprocess.check_call(["wsl", "sudo", "apt", "install", pkg, "-y"])
            return

        elif "choco" in packages[pkg] and sys.platform == "win32":
            _choco_install(pkg)
            return

    raise Exception(f"{pkg} cannot be found.")


def install_package(pkg, wsl=False):
    require_package(pkg, wsl=wsl)


def _is_go_package_installed(go_pkg_path):
    return (
        subprocess.call(
            [
                "go",
                "version",
                "-m",
                os.path.join(
                    get_home_path(),
                    "go",
                    "bin",
                    go_pkg_path.split("/")[-1].split("@")[0],
                ),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def _choco_install(pkg, upgrade=False):
    pkg = packages[pkg]["choco"]["packageName"]

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


def open_log_file(file):
    klogg = find_executable("klogg")
    if klogg:
        start_process([klogg, "--follow", file])
