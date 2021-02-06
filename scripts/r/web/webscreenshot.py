from pyppeteer import launch
import asyncio
import os
from _shutil import shell_open, get_files
import sys
import time


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


def webscreenshot(html_file, out_file=None, javascript=None, debug=False):
    if out_file is None:
        out_file = os.path.splitext(html_file)[0] + ".png"

    async def main():
        browser = await launch(
            headless=False,
            executablePath=r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
            args=["--enable-font-antialiasing", "--font-render-hinting=max", "--force-device-scale-factor=1"],
        )
        page = await browser.newPage()

        # await page.setViewport({
        #     'width': int(im_size[0] / SCALE),
        #     'height': int(im_size[1] / SCALE),
        #     'deviceScaleFactor': SCALE,
        # })

        await page.setViewport({"width": 1920, "height": 2000})

        await page.goto(
            "file://" + os.path.realpath(html_file).replace("\\", "/"),
            waitUntil="networkidle0",
        )

        if javascript:
            await page.evaluate("() => { %s }" % javascript)

        if debug:
            input("press any key to exit...")

        # Screenshot DOM element only
        element = await page.querySelector("body")
        screenshot_params = {"path": out_file, "omitBackground": True}

        await element.screenshot(screenshot_params)
        # await screenshotDOMElement(page=page, selector="table", path=out_file)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    return out_file


if __name__ == "__main__":
    f = get_files()[0]
    out = webscreenshot(f)
    shell_open(out)
