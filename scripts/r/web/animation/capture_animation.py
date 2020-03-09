import asyncio
from pyppeteer import launch
import time
import sys
from _shutil import *

if True:
    sys.path.append('../../video')
    from ccapture_to_mov import convert_to_mov

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall


def capture_js_animation(url, out_file=None):
    async def main():
        browser = await launch(headless=False,
                               args=['--disable-dev-shm-usage'],
                               executablePath=r"C:\Program Files (x86)\Chromium\Application\chrome.exe")
        page = await browser.newPage()
        await page.goto(url)

        time.sleep(1.0)

        print('Start capture.')
        await page.evaluate('() => { window.startCapture(); }')

        await page.waitForXPath("//*[@id='captureStatus' and contains(., 'stopped')]", timeout=0)

        # TODO: Wait until file is saved
        time.sleep(1)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())
    tar_file = sorted(glob.glob(os.path.expanduser('~/Downloads/*.tar')),
                      key=os.path.getmtime, reverse=True)[0]
    return convert_to_mov(tar_file, fps=25, out_file=out_file)


if __name__ == "__main__":
    capture_js_animation('http://localhost:8080/' + '{{HTML_FILE}}')