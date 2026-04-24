import os
import sys
from typing import List

WEZTERM_EXECUTABLE = r"C:\Program Files\WezTerm\wezterm.exe"
WEZTERM_CONFIG = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "settings", "wezterm", "wezterm.lua"
    )
)


def wrap_args_wezterm(
    args,
    title=None,
    cwd=None,
    maximized=False,
    **kwargs,
) -> List[str]:
    if sys.platform != "win32":
        raise OSError(f"{sys.platform} is not supported")

    wezterm_args = [WEZTERM_EXECUTABLE, "--config-file", WEZTERM_CONFIG, "start"]

    if maximized:
        os.environ["WEZTERM_MAXIMIZED"] = "1"
    elif "WEZTERM_MAXIMIZED" in os.environ:
        del os.environ["WEZTERM_MAXIMIZED"]

    if cwd:
        wezterm_args += ["--cwd", cwd]

    if title:
        os.environ["WEZTERM_WINDOW_TITLE"] = title

    wezterm_args += ["--"] + args

    return wezterm_args
