import logging
import sys

from _script import Script, get_all_scripts, run_script
from r.speech_to_text import speech_to_text
from utils.logger import setup_logger

from scripts.r.ai.usetool import use_tool


def _match_fuzzy(item: str, patt: str) -> bool:
    patt = patt.lower()
    if not patt:
        return True
    else:
        return all([(x in str(item).lower()) for x in patt.split(" ")])


def find_tool(kw: str) -> str:
    """Fuzzy search using space-separated keywords. The function returns the matched tool path."""

    scripts_path = get_all_scripts()
    scripts_path = [x for x in scripts_path if _match_fuzzy(x, kw)]
    scripts = [Script(s) for s in scripts_path]
    scripts = sorted(scripts)
    return [x.script_path for x in scripts][0]


def run_tool(path: str) -> None:
    run_script(path)


def _main():
    text = speech_to_text()
    if text is None:
        sys.exit(1)

    result = use_tool(text, tools=[find_tool, run_tool])
    logging.debug(f"Result: {result}")


if __name__ == "__main__":
    setup_logger()
    _main()
