import argparse
import hashlib
import os
import subprocess
import time


def web_fetch(url: str) -> str:
    """
    Fetch the content of a web page from the given URL.
    """
    cache_dir = os.path.join(os.getcwd(), "tmp", "web_fetch_cache")
    os.makedirs(cache_dir, exist_ok=True)

    url_hash = hashlib.sha256(url.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, url_hash)

    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if time.time() - mtime < 600:  # 10 minutes
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()

    result = subprocess.run(
        ["run_script", "r/web/browsercontrol/browsercontrol.js", "get-markdown", url],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0 and not result.stdout:
        return f"Error: failed to fetch {url}"

    content = result.stdout
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(content)

    return content


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    print(web_fetch(args.url))
