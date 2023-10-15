import logging
import os
import subprocess
import sys
from typing import Dict

from _shutil import get_home_path, prepend_to_path


def _get_venv_bin_path(venv_path: str) -> str:
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts")
    else:
        return os.path.join(venv_path, "bin")


def _get_python_venv_path(venv_name: str) -> str:
    venv_path = os.path.expanduser(os.path.join(get_home_path(), ".venv", venv_name))
    if not os.path.exists(venv_path):
        create_venv_args = [sys.executable, "-m", "venv", venv_path]
        logging.debug(f"Create Python venv: {create_venv_args}")
        subprocess.check_call(create_venv_args)
    return venv_path


def activate_python_venv(venv_name: str, env: Dict[str, str]):
    venv_path = _get_python_venv_path(venv_name)

    # If Python is running in a virtual environment (venv), ensure that the
    # shell executes the Python version located inside the venv.)
    prepend_to_path(_get_venv_bin_path(venv_path=venv_path), env=env)


def get_venv_python_executable(venv_name: str) -> str:
    venv_path = _get_python_venv_path(venv_name)
    bin_path = _get_venv_bin_path(venv_path=venv_path)
    if sys.platform == "win32":
        return os.path.join(bin_path, "python.exe")
    else:
        return os.path.join(bin_path, "python")
