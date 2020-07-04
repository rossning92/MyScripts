from _shutil import *
from pyppeteer import launch
from r.video.ccapture_to_mov import convert_to_mov
from r.web.animation.start_webpack_server import start_server
import asyncio
import sys
import time
import urllib

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall


def capture_js_animation(in_file, out_file=None, params=None):
    assert in_file.lower().endswith(".js")

    ps = start_server(in_file)

    name = os.path.basename(os.path.splitext(in_file)[0])
    print("Generating animation: %s" % name + ".mp4")
    url = "http://localhost:8080/%s.html" % name

    if params:
        url = (
            url
            + "?"
            + "&".join(
                ["%s=%s" % (k, urllib.parse.quote(v)) for k, v in params.items()]
            )
        )

    if out_file is None:
        out_file = "animation_%s.mov" % get_time_str()
    prefix, ext = os.path.splitext(out_file)

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
                "downloadPath": os.path.abspath(os.path.dirname(prefix)),
            },
        )

        await page.goto(url)

        time.sleep(1.0)

        print("Start capture.")
        await page.evaluate(
            '() => { window.startCapture({name: "%s"}); }' % os.path.basename(prefix)
        )

        await page.waitForXPath(
            "//*[@id='captureStatus' and contains(., 'stopped')]", timeout=0
        )

        while not exists(prefix + ".tar"):
            time.sleep(0.5)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    tar_file = prefix + ".tar"
    if not out_file.endswith(".tar"):
        result = convert_to_mov(tar_file, fps=25, out_file=prefix + ext)
        os.remove(tar_file)
    else:
        result = tar_file

    ps.kill()

    return result


if __name__ == "__main__":
    cd(expanduser("~/Downloads"))

    f = get_files()[0]
    assert f.endswith(".js")
    out_file = os.path.splitext(f)[0] + ".mp4"

    capture_js_animation(f, out_file=out_file)

