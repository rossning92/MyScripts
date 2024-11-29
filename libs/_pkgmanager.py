import glob
import logging
import os
import shutil
import subprocess
import sys
from functools import lru_cache
from typing import Dict, List, Optional

from _shutil import (
    check_output,
    get_home_path,
    is_in_termux,
    prepend_to_path,
    refresh_env_vars,
    run_elevated,
    start_process,
)
from utils.jsonutil import load_json

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


def get_all_available_packages() -> List[str]:
    return [name for name in packages.keys()]


def require_package(
    pkg: str,
    wsl=False,
    env: Optional[Dict[str, str]] = None,
    force_install=False,
    upgrade=False,
):
    if "dependantPackages" in packages:
        for pkg in packages["dependantPackages"]:
            require_package(pkg)

    if pkg in packages:
        if "golang" in packages[pkg]:
            require_package("golang")
            if "packagePath" in packages[pkg]["golang"]:
                go_pkg_path = packages[pkg]["golang"]["packagePath"]
                if not _is_go_package_installed(go_pkg_path) or force_install:
                    logging.info(f"Installing go package: {go_pkg_path}...")
                    subprocess.check_call(["go", "install", go_pkg_path])
                return

        elif "npm" in packages[pkg]:
            for p in packages[pkg]["npm"]["packages"]:
                if not is_npm_global_package_installed(p) or force_install:
                    logging.info(f"Installing package using npm: {p}")
                    subprocess.check_call(
                        (["sudo"] if sys.platform == "linux" else [])
                        + ["npm", "install", "-g", p],
                        shell=sys.platform == "win32",
                    )
            return

        elif "yarn" in packages[pkg]:
            for p in packages[pkg]["yarn"]["packages"]:
                logging.info(f"Installing package using npm: {p}")
                subprocess.check_call(["yarn", "global", "add", p])
                yarn_global_bin_path = subprocess.check_output(
                    ["yarn", "global", "bin"], universal_newlines=True
                ).strip()
                prepend_to_path(
                    yarn_global_bin_path,
                    env=env,
                )
            return

        elif "pacman" in packages[pkg] and shutil.which("pacman"):
            for p in packages[pkg]["pacman"]["packages"]:
                if (
                    subprocess.call(
                        ["pacman", "-Q", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT,
                    )
                    != 0
                ) or force_install:
                    logging.info(f"Installing package using pacman: {p}")
                    subprocess.check_call(["sudo", "pacman", "-S", "--noconfirm", p])
            return

        elif "dnf" in packages[pkg] and shutil.which("dnf"):
            for p in packages[pkg]["dnf"]["packages"]:
                if (
                    subprocess.call(
                        ["dnf", "list", "installed", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    != 0
                ) or force_install:
                    logging.info(f"Installing package using dnf: {p}")
                    subprocess.check_call(["sudo", "dnf", "install", "-y", p])
            return

        elif "yay" in packages[pkg] and shutil.which("pacman"):
            yay_packages = packages[pkg]["yay"]["packages"]
            for p in yay_packages:
                if (
                    subprocess.call(
                        ["yay", "-Q", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT,
                    )
                    != 0
                ) or force_install:
                    logging.info(f"Installing package using yay: {p}")
                    subprocess.check_call(["yay", "-S", "--noconfirm", "--rebuild", p])
            return

        elif is_in_termux() and "termux" in packages[pkg]:
            for p in packages[pkg]["termux"]["packages"]:
                if (
                    subprocess.call(
                        ["dpkg", "-s", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT,
                    )
                    != 0
                ) or force_install:
                    logging.warning(f'Package "{p}" was not found, installing...')
                    subprocess.check_call(["pkg", "install", p, "-y"])
            return

        elif wsl and "apt" in packages[pkg]:
            wsl_cmd = ["wsl"] if wsl and sys.platform == "win32" else []
            for p in packages[pkg]["apt"]["packages"]:
                if (
                    subprocess.call(
                        wsl_cmd + ["dpkg", "-s", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT,
                    )
                    != 0
                ) or force_install:
                    if "ppa" in packages[pkg]["apt"]:
                        ppa = packages[pkg]["apt"]["ppa"]
                        assert isinstance(ppa, str)
                        subprocess.check_call(
                            wsl_cmd + ["sudo", "add-apt-repository", f"ppa:{ppa}", "-y"]
                        )
                        subprocess.check_call(wsl_cmd + ["sudo", "apt-get", "update"])

                    logging.info(f"Installing package using apt: {pkg}...")
                    subprocess.check_call(wsl_cmd + ["sudo", "apt", "install", "-y", p])
            return

        elif "dotnet" in packages[pkg]:
            for p in packages[pkg]["dotnet"]["packages"]:
                if (
                    subprocess.call(
                        ["dotnet", "tool", "list", "--global", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT,
                    )
                    != 0
                ) or force_install:
                    logging.info(f"Installing dotnet package package: {p}...")
                    subprocess.check_call(["dotnet", "tool", "install", "--global", p])
            if sys.platform == "win32":
                prepend_to_path(
                    os.path.expandvars("%USERPROFILE%\\.dotnet\\tools"), env=env
                )
            else:
                prepend_to_path(os.path.expandvars("$HOME/.dotnet/tools"), env=env)

            return

        elif sys.platform == "win32" and "choco" in packages[pkg]:
            _choco_install(pkg, force_install=force_install, upgrade=upgrade)
            return

        elif "pip" in packages[pkg]:
            for p in packages[pkg]["pip"]["packages"]:
                # Check if pip package is installed
                ret = (
                    subprocess.call(
                        [sys.executable, "-m", "pip", "show", p],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    or force_install
                )
                if ret != 0:
                    logging.info(f"Installing pip package: {p}...")
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "--upgrade", p]
                    )
            return

    raise Exception(f"{pkg} cannot be found.")


@lru_cache(maxsize=None)
def is_npm_global_package_installed(p):
    return (
        subprocess.call(
            ["npm", "list", "-g", p],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            shell=sys.platform == "win32",
            creationflags=(
                subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            ),  # prevent title change
        )
        == 0
    )


def install_package(pkg, wsl=False):
    logging.info(f"Install package: {pkg}")
    require_package(pkg, wsl=wsl)


def _is_go_package_installed(go_pkg_path):
    executable_path = go_pkg_path.split("/")[-1].split("@")[0]
    if sys.platform == "win32":
        executable_path += ".exe"

    return os.path.exists(
        os.path.join(
            get_home_path(),
            "go",
            "bin",
            executable_path,
        )
    )


def _choco_is_package_installed(name: str) -> bool:
    use_builtin_choco_command = False
    if use_builtin_choco_command:
        # Note that the "--localonly" option has been removed in Chocolatey 2.0 and higher.
        out = check_output(["choco", "list", "--exact", "--localonly", name])
        return "0 packages installed" not in out
    else:
        path = shutil.which("choco")
        if path:
            lib_path = os.path.abspath(os.path.dirname(path) + f"\\..\\lib\\{name}")
            return os.path.exists(lib_path)
        else:
            raise Exception("choco is not installed.")


def _choco_install(pkg, upgrade=False, force_install=True):
    for p in packages[pkg]["choco"]["packages"]:
        if not _choco_is_package_installed(p) or force_install:
            logging.info("Install `%s`..." % p)
            args = ["choco", "install", p, "-y", "-s", "https://chocolatey.org/api/v2/"]
            if force_install:
                args.append("-f")
            run_elevated(args)

        elif upgrade or force_install:
            logging.info("Upgrade `%s`..." % p)
            args = ["choco", "upgrade", p, "-y", "-s", "https://chocolatey.org/api/v2/"]
            if force_install:
                args.append("-f")
            run_elevated(args)

        else:
            logging.debug(f"Package {p} already exists, skip installation.")

    refresh_env_vars()


def open_log_file(file):
    klogg = find_executable("klogg")
    if klogg:
        start_process([klogg, "--follow", file])
