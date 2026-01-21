import argparse
import urllib.parse

from .web_fetch import web_fetch


def web_search(query: str) -> str:
    """Perform web searches to gather information for user questions.

    - Queries should be: Keywords (not full sentences) and SEO-friendly.
    - Start with broad queries for an overview. Follow with narrow, specific queries based on the results. You can call the tool multiple times if needed.
    """

    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    return web_fetch(url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    print(web_search(args.query))
