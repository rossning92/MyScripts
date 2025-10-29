import asyncio
import os
import sys
import time
from typing import Optional

from _shutil import cd, get_files
from pyppeteer import launch

from videoedit.start_movy_server import start_server

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall

PORT = 5555


def export_movy_animation(file: str, out_file: Optional[str] = None):
    print("Render animation: %s..." % file)

    download_dir = os.path.abspath(
        os.path.dirname(out_file) if out_file else os.path.dirname(file)
    )

    if out_file:
        root, ext = os.path.splitext(out_file)
        base_name = os.path.basename(root)
    else:
        root, ext = os.path.splitext(file)
        base_name = os.path.basename(root)
        out_file = os.path.join(download_dir, base_name + ".webm")
    if ext == ".webm":
        format = "webm"
    elif ext == ".tar":
        format = "png"
    else:
        raise Exception(f"Invalid output file extension: {ext}")

    assert file.lower().endswith(".js")

    ps = start_server(file, port=PORT, dev=False)

    url = "http://localhost:%d/?file=%s" % (PORT, os.path.basename(file))

    async def main():
        browser = await launch(
            headless=False,
            args=["--disable-dev-shm-usage"],
            executablePath=(
                r"C:\Program Files\Chromium\Application\chrome.exe"
                if sys.platform == "win32"
                else "chromium"
            ),
        )
        page = await browser.newPage()

        await page._client.send(
            "Page.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": download_dir,
            },
        )

        await page.goto(url)

        await page.waitForFunction(
            'document.querySelector("body").innerText.includes("EXPORT")'
            '&& !document.querySelector("body").innerText.includes("LOADING")'
        )
        time.sleep(0.5)

        print("Start capture.")
        await page.evaluate("window.exportVideo({format:'%s'})" % format)

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

    file = get_files()[0]
    assert file.endswith(".js")

    export_movy_animation(file)
