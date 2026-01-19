import argparse
import subprocess

from utils.file_cache import file_cache


@file_cache(cache_dir_name="web_fetch_cache")
def web_fetch(url: str) -> str:
    """
    Fetch the content of a web page from the given URL.
    """
    result = subprocess.run(
        ["run_script", "r/web/browsercontrol/browsercontrol.js", "get-markdown", url],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0 and not result.stdout:
        return f"Error: failed to fetch {url}"

    return result.stdout


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    print(web_fetch(args.url))
