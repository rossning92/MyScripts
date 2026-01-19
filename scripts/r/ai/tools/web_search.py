import argparse
import subprocess
import urllib.parse


def web_search(query: str) -> str:
    """Perform web searches to gather information for user questions.

    - Queries should be: Keywords (not full sentences) and SEO-friendly.
    - Start with broad queries for an overview. Follow with narrow, specific queries based on the results. You can call the tool multiple times if needed.
    """

    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"

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
    parser.add_argument("query")
    args = parser.parse_args()
    print(web_search(args.query))
