import asyncio
from pyppeteer import launch
import time
import sys
from _shutil import *

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall

name = '{{_NAME}}'

if True:
    sys.path.append('../../video')
    from ccapture_to_mov import convert_to_mov


async def main():
    browser = await launch(headless=False,
                           args=['--disable-dev-shm-usage'])
    page = await browser.newPage()
    url = 'http://localhost:8080'
    if name:
        url += '/%s.html' % name
    await page.goto(url)

    time.sleep(1.0)

    print('Start capture.')
    await page.evaluate('() => { window.startCapture(); }')

    await page.waitForXPath("//*[@id='captureStatus' and contains(., 'stopped')]", timeout=0)

    # Wait until file is saved
    time.sleep(2)

    await browser.close()


asyncio.get_event_loop().run_until_complete(main())
tar_file = sorted(glob.glob(os.path.expanduser('~/Downloads/*.tar')),
                  key=os.path.getmtime, reverse=True)[0]
convert_to_mov(tar_file, fps=25)
