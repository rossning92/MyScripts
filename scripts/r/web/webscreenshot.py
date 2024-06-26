import argparse
import asyncio

from pyppeteer import launch


async def main(url: str):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url)
    await page.screenshot({"path": "screenshot.png"})
    await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    asyncio.get_event_loop().run_until_complete(main(args.url))
