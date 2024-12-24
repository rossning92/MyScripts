# https://github.com/unclecode/crawl4ai

import argparse
import asyncio
import importlib.util
import subprocess
import sys

if not importlib.util.find_spec("crawl4ai"):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "crawl4ai"])

from crawl4ai import AsyncWebCrawler
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def read_webpage(url: str) -> str:
    async def crawl():
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter(
                        threshold=0.48, threshold_type="fixed", min_word_threshold=0
                    )
                ),
            )
            markdown = result.markdown_v2
            if markdown:
                return markdown.raw_markdown
            else:
                return "nothing"

    return asyncio.run(crawl())


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    content = read_webpage(args.url)
    print(content)


if __name__ == "__main__":
    _main()
