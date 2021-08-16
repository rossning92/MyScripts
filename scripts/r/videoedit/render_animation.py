from _shutil import *
from pyppeteer import launch
from video.ccapture_to_mov import convert_to_mov
from videoedit.start_movy_server import start_server
import asyncio
import sys
import time
import urllib

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall

PORT = 5555


def render_animation(file):
    print("Render animation: %s..." % file)

    assert file.lower().endswith(".js")

    ps = start_server(file, port=PORT)

    url = "http://localhost:%d" % PORT

    async def main():
        browser = await launch(
            headless=False,
            args=["--disable-dev-shm-usage"],
            executablePath=r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
        )
        page = await browser.newPage()

        await page._client.send(
            "Page.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": os.path.abspath(os.path.dirname(file)),
            },
        )

        await page.goto(url)

        time.sleep(1)

        print("Start capture.")
        await page.evaluate("() => { window.movy.startRender(); }")

        while await page.evaluate("() => window.movy.isRendering"):
            time.sleep(0.5)

        # Make sure the video file is saved
        time.sleep(1)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    ps.kill()

    return os.path.splitext(file)[0] + ".mov"


if __name__ == "__main__":
    cd(expanduser("~/Downloads"))

    if "{{_FORMAT}}":
        format = "{{_FORMAT}}"
    else:
        format = "mp4"

    file = get_files()[0]
    assert file.endswith(".js")

    render_animation(file)

