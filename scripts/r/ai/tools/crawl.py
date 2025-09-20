# https://github.com/unclecode/crawl4ai
# Prerequisite: run_script r/ai/run_crawl4ai_docker.sh

import argparse

import requests


def crawl(url: str) -> str:
    """
    The tool takes a URL, crawls it, and converts it into clean markdown data.
    """
    headers = {"Content-Type": "application/json"}
    data = {"url": url, "f": "raw", "q": None, "c": "0"}

    response = requests.post("http://localhost:11235/md", headers=headers, json=data)
    return response.json()["markdown"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str, nargs="?", default="https://example.com/")

    args = parser.parse_args()

    print(crawl(args.url))
