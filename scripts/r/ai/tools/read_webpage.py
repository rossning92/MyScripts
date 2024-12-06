# https://github.com/unclecode/crawl4ai

import asyncio

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
            content = result.markdown_v2.raw_markdown
            return content

    return asyncio.run(crawl())
