from _shutil import *
from pyppeteer import launch
from r.video.ccapture_to_mov import convert_to_mov
import asyncio
import sys
import time

# Fix for `callFunctionOn: Target closed.`
# pip3 install websockets==6.0 --force-reinstall


def capture_js_animation(url, out_file=None, output_video_file=True):
    if out_file is None:
        out_file = 'animation_%s' % get_time_str()

    async def main():
        browser = await launch(headless=False,
                               args=['--disable-dev-shm-usage'],
                               executablePath=r"C:\Program Files (x86)\Chromium\Application\chrome.exe")
        page = await browser.newPage()

        await page._client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': os.path.abspath(os.path.dirname(out_file))
        })

        await page.goto(url)

        time.sleep(1.0)

        print('Start capture.')
        await page.evaluate('() => { window.startCapture({name: "%s"}); }' % os.path.basename(out_file))

        await page.waitForXPath("//*[@id='captureStatus' and contains(., 'stopped')]", timeout=0)

        # TODO: Wait until file is saved
        time.sleep(1)

        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

    tar_file = out_file + '.tar'
    if output_video_file:
        result = convert_to_mov(tar_file, fps=25, out_file=out_file)
        os.remove(tar_file)
    else:
        result = tar_file

    return result


if __name__ == "__main__":
    cd(expanduser('~/Downloads'))
    capture_js_animation('http://localhost:8080/' + '{{HTML_FILE}}',
                         output_video_file=bool('{{_OUTPUT_VID_FILE}}'))
