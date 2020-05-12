from pyppeteer import launch
import asyncio
import os
from _shutil import open_directory


def webscreenshot(html_file, out_file=None):
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

        await page.goto("file://" + os.path.realpath(html_file).replace("\\", "/"))

        screenshot_params = {"path": out_file, "omitBackground": True}
        # await page.screenshot(screenshot_params)

        # Screenshot DOM element only
        element = await page.querySelector("body")
        await element.screenshot(screenshot_params)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    return out_file


if __name__ == "__main__":
    out = webscreenshot(r"{{_FILE}}")
    open_directory(out)
