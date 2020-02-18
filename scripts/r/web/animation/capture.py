import asyncio
from pyppeteer import launch
import time
import sys
from _shutil import *

if True:
    sys.path.append('../../video')
    from ccapture_to_mov import convert_to_mov


async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto('http://localhost:8080')
    await page.screenshot({'path': 'example.png'})

    await page.evaluate('() => { window.startCapture(); }')

    await page.waitForXPath("//*[@id='captureStatus' and contains(., 'stopped')]")

    # Wait until file is saved
    time.sleep(2)

    await browser.close()


asyncio.get_event_loop().run_until_complete(main())
tar_file = sorted(glob.glob(os.path.expanduser('~/Downloads/*.tar')),
                  key=os.path.getmtime, reverse=True)[0]
convert_to_mov(tar_file, fps=25)
