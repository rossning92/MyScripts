import argparse
import urllib.parse

from .web_fetch import web_fetch


def web_search(query: str) -> str:
    """Perform web searches to gather information for user questions.
    - You can call this tool multiple times to gather enough information.
    - Start with broader queries to get an overview, then narrow down with more specific queries based on the results you receive.
    - You can use `after:YYYY-MM-DD` to limit results to after a given date.
    - Your query should be keywords (not full sentences) and SEO-friendly.
    """

    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    return web_fetch(url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    print(web_search(args.query))
