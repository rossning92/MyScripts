import argparse
import subprocess

from utils.file_cache import file_cache
from utils.menu.shellcmdmenu import ShellCmdMenu
from utils.menu.textmenu import TextMenu


class FetchRetryMenu(TextMenu):
    def __init__(self, error_message: str, prompt: str):
        super().__init__(
            text=error_message,
            prompt=f"{prompt}\n([r]etry, [d]ebug)",
            prompt_color="red",
        )
        self.should_retry = False
        self.add_command(self.retry, hotkey="r")
        self.add_command(self.debug, hotkey="d")

    def retry(self):
        self.should_retry = True
        self.close()

    def debug(self):
        self.run_raw(
            lambda: subprocess.run(
                ["run_script", "r/web/browsercli/browsercli.js", "debug"]
            )
        )


@file_cache(cache_dir_name="web_fetch_cache")
def web_fetch(url: str) -> str:
    """
    Fetch the content of a web page from the given URL.
    """
    while True:
        menu = ShellCmdMenu(
            command=[
                "run_script",
                "r/web/browsercli/browsercli.js",
                "get-markdown",
                url,
            ],
            prompt=f"fetching: {url}",
        )
        menu.exec()

        returncode = menu.get_returncode()
        stdout = menu.get_output()

        if returncode == 0 and stdout:
            return stdout

        error_message = stdout
        menu = FetchRetryMenu(
            error_message=error_message,
            prompt=f"failed to fetch {url}",
        )
        menu.exec()
        if not menu.should_retry:
            raise Exception(error_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    print(web_fetch(args.url))
