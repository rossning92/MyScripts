import argparse
import os

import requests


def google_search(
    query, api_key=os.environ["GOOGLE_API_KEY"], cse_id=os.environ["GOOGLE_CSE_ID"]
):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}"
    response = requests.get(search_url)
    if response.status_code == 200:
        search_results = response.json()
        return search_results
    else:
        response.raise_for_status()
        raise Exception(f"Error occurred: {response.status_code}")


def print_google_search(query: str):
    results = google_search(query)
    if "items" in results:
        for item in results["items"]:
            title = item["title"]
            link = item["link"]
            print(f"[{title}]({link})")
            if "snippet" in item:
                print(item["snippet"])
            print()
    else:
        print("No results found")


def main():
    parser = argparse.ArgumentParser(description="Perform a Google search.")
    parser.add_argument("query", type=str, help="The search query")
    args = parser.parse_args()

    print_google_search(args.query)


if __name__ == "__main__":
    main()
