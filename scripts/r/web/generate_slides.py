from _shutil import *
import asyncio
from pyppeteer import launch
from _script import *
from _gui import *
import webbrowser

try_import('markdown2', pkg_name='markdown2')
import markdown2

try_import('slugify', pkg_name='python-slugify')
from slugify import slugify

SCALE = 1
GEN_HTML = '{{GEN_HTML}}'
REGENERATE = True


def write_to_file(text, file_name, template_file):
    template = templateEnv.get_template(template_file)
    html = template.render({'text': text})  # this is where to put args to the template renderer

    if GEN_HTML:
        html_file_name = file_name + '.html'
        with open(html_file_name, 'w') as f:
            f.write(html)
        webbrowser.open(html_file_name)
    else:
        async def main():
            browser = await launch(headless=False)
            page = await browser.newPage()
            await page.setViewport({
                'width': int(1920 / SCALE),
                'height': int(1080 / SCALE),
                'deviceScaleFactor': SCALE,
            })
            # await page.goto('file://' + os.path.realpath(f).replace('\\', '/'))
            await page.goto('data:text/html,' + html)
            await page.screenshot({'path': file_name, 'omitBackground': True})
            await browser.close()

        asyncio.get_event_loop().run_until_complete(main())


if __name__ == '__main__':
    templateLoader = jinja2.FileSystemLoader(searchpath=os.getcwd())
    templateEnv = jinja2.Environment(loader=templateLoader)

    in_file = get_files()[0]
    in_file_name = os.path.splitext(os.path.basename(in_file))[0]
    template_file = in_file_name + '.html'
    if not os.path.exists(template_file):
        # Specify template file from parameter
        template_file = '{{GS_TEMPLATE}}'
        if not template_file:
            templates = list(sorted(glob.glob('*.html')))
            i = search(templates)
            template_file = templates[i]
            set_variable('GS_TEMPLATE', template_file)

    out_folder = os.path.dirname(in_file)

    with open(in_file, encoding='utf-8') as f:
        s = f.read()
    slides = s.split('---')
    slides = [x.strip() for x in slides]

    for slide in slides:
        out_file = os.path.join(out_folder, slugify(slide) + '.png')
        if REGENERATE or (not os.path.exists(out_file)):
            print2('Generate %s ...' % out_file)

            markdown_text = markdown2.markdown(slide, extras=['break-on-newline', 'fenced-code-blocks'])
            print(markdown_text)
            write_to_file(markdown_text,
                          out_file,
                          template_file)
