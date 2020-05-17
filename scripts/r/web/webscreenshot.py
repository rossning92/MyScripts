from pyppeteer import launch
import asyncio
import os
from _shutil import open_directory
import sys


def webscreenshot(html_file, out_file=None, javascript=None, debug=False):
    if out_file is None:
        out_file = os.path.splitext(html_file)[0] + ".png"

    async def screenshotDOMElement(*, page, selector, path):
        rect = await page.evaluate(
            """selector => {
            const element = document.querySelector(selector);
            const {x, y, width, height} = element.getBoundingClientRect();
            return {left: x, top: y, width, height, id: element.id};
        }""",
            selector,
        )

        return await page.screenshot(
            {
                "path": path,
                "clip": {
                    "x": rect["left"],
                    "y": rect["top"],
                    "width": rect["width"],
                    "height": rect["height"],
                },
            }
        )

    async def main():
        browser = await launch(
            headless=False,
            executablePath=r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
        )
        page = await browser.newPage()

        # await page.setViewport({
        #     'width': int(im_size[0] / SCALE),
        #     'height': int(im_size[1] / SCALE),
        #     'deviceScaleFactor': SCALE,
        # })

        await page.setViewport({'width': 1920, 'height': 1080})

        await page.goto("file://" + os.path.realpath(html_file).replace("\\", "/"))

        if javascript:
            await page.evaluate("() => { %s }" % javascript)

        if debug:
            input("press any key to exit...")
            sys.exit(0)

        # Screenshot DOM element only
        element = await page.querySelector("body")
        screenshot_params = {"path": out_file, "omitBackground": True}
        await element.screenshot(screenshot_params)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    return out_file


if __name__ == "__main__":
    out = webscreenshot(
        r"{{_FILE}}", javascript="setCode('hello, world!'); markText(0, 0, 0, 5);"
    )
    open_directory(out)
