import subprocess


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
