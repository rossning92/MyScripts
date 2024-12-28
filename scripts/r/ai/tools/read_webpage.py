# https://github.com/unclecode/crawl4ai
# Prerequisite: run_script r/ai/run_crawl4ai_docker.sh

import argparse
import json

import requests


def read_webpage(url: str) -> str:
    response = requests.post(
        "http://localhost:11235/crawl_sync",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer your_secret_token",
        },
        data=json.dumps({"urls": url}),
    )
    result = response.json()
    return result["result"]["markdown"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)

    args = parser.parse_args()

    print(read_webpage(args.url))
