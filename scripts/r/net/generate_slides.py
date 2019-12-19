from _shutil import *
import asyncio
from pyppeteer import launch
import jinja2
from _script import *
from _gui import *

try_import('slugify', pkg_name='python-slugify')
from slugify import slugify

FILE_PREFIX = 'function_title'

SCALE = 1


def write_to_file(text, file_name):
    template = templateEnv.get_template(TEMPLATE_FILE)
    a = template.render({'text': text})  # this is where to put args to the template renderer

    async def main():
        browser = await launch()
        page = await browser.newPage()
        await page.setViewport({
            'width': int(1920 / SCALE),
            'height': int(1080 / SCALE),
            'deviceScaleFactor': SCALE,
        })
        # await page.goto('file://' + os.path.realpath(f).replace('\\', '/'))
        await page.goto('data:text/html,' + a)
        await page.screenshot({'path': file_name, 'omitBackground': True})
        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())


if __name__ == '__main__':
    templateLoader = jinja2.FileSystemLoader(searchpath=os.getcwd())
    templateEnv = jinja2.Environment(loader=templateLoader)

    TEMPLATE_FILE = '{{GS_TEMPLATE}}'
    if not TEMPLATE_FILE:
        templates = list(sorted(glob.glob('*.html')))
        i = search(templates)
        TEMPLATE_FILE = templates[i]
        set_variable('GS_TEMPLATE', TEMPLATE_FILE)

    in_file = get_files()[0]
    out_folder = os.path.dirname(in_file)

    with open(in_file, encoding='utf-8') as f:
        s = f.read()
    slides = s.split('---')
    slides = [x.strip() for x in slides]

    for slide in slides:
        out_file = os.path.join(out_folder, slugify(slide) + '.png')
        if not os.path.exists(out_file):
            print2('Generate %s ...' % out_file)
            write_to_file(slide, out_file)
