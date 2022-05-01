import asyncio
import os
import time

from _shutil import cd, get_files
from pyppeteer import launch

from videoedit.start_movy_server import start_server

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall

PORT = 5555


def export_movy_animation(file):
    print("Render animation: %s..." % file)

    assert file.lower().endswith(".js")

    ps = start_server(file, port=PORT, dev=False)

    url = "http://localhost:%d/?file=%s" % (PORT, os.path.basename(file))

    out_file = None

    async def main():
        nonlocal out_file

        browser = await launch(
            headless=False,
            args=["--disable-dev-shm-usage"],
            executablePath=r"C:\Program Files\Chromium\Application\chrome.exe",
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
            'document.querySelector("body").innerText.includes("EXPORT")'
            '&& !document.querySelector("body").innerText.includes("LOADING")'
        )
        time.sleep(0.5)

        print("Start capture.")
        await page.keyboard.down("Control")
        await page.keyboard.press("KeyM")
        await page.keyboard.up("Control")

        # Waiting until the video file is saved.
        print("Rendering to %s" % out_file, end="")
        while not os.path.exists(out_file):
            print(".", end="")
            time.sleep(1)
        print()
        time.sleep(1)

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

    export_movy_animation(file)

