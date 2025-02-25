import argparse
import os
from io import StringIO

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


def get_google_search_result(query: str) -> str:
    results = google_search(query)
    output = StringIO()
    if "items" in results:
        for item in results["items"]:
            title = item["title"]
            link = item["link"]
            output.write(f"[{title}]({link})\n")
            if "snippet" in item:
                output.write(item["snippet"] + "\n")
            output.write("\n")
    else:
        output.write("No results found")
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description="Perform a Google search.")
    parser.add_argument("query", type=str, help="The search query")
    args = parser.parse_args()

    result = get_google_search_result(args.query)
    print(result)


if __name__ == "__main__":
    main()
