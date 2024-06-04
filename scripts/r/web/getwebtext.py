import argparse
import asyncio

from pyppeteer import launch


async def main(url: str):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)

    # Extracting text content from the page
    content = await page.evaluate("document.body.innerText", force_expr=True)
    print(content)

    await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(args.url))
