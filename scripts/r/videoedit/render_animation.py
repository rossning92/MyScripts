import asyncio
from genericpath import exists
import os
import time

from _shutil import cd, get_files
from pyppeteer import launch

from videoedit.start_movy_server import start_server

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall

PORT = 5555


def render_animation(file):
    print("Render animation: %s..." % file)

    assert file.lower().endswith(".js")

    ps = start_server(file, port=PORT)

    url = "http://localhost:%d" % PORT

    out_file = None

    async def main():
        nonlocal out_file

        browser = await launch(
            headless=False,
            args=["--disable-dev-shm-usage"],
            executablePath=r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
        )
        page = await browser.newPage()
        download_dir = os.path.abspath(os.path.dirname(file))
        out_file = os.path.join(download_dir, os.path.splitext(file)[0] + ".webm")

        await page._client.send(
            "Page.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": os.path.abspath(os.path.dirname(file)),
            },
        )

        await page.goto(url)

        await page.waitForFunction(
            'document.querySelector("body").innerText.includes("render")'
        )

        print("Start capture.")
        await page.evaluate("() => { window.movy.startRender(); }")

        while await page.evaluate("() => window.movy.isRendering"):
            time.sleep(0.5)

        # Make sure the video file is saved
        while not exists(out_file):
            time.sleep(0.5)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    ps.kill()

    return out_file


if __name__ == "__main__":
    cd(os.path.expanduser("~/Downloads"))

    if "{{_FORMAT}}":
        format = "{{_FORMAT}}"
    else:
        format = "mp4"

    file = get_files()[0]
    assert file.endswith(".js")

    render_animation(file)

