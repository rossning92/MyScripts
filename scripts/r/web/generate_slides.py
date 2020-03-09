from _gui import *
from _script import *
from _shutil import *
from pyppeteer import launch
import asyncio
import markdown2
import webbrowser

SCALE = 1
GEN_HTML = bool('{{GEN_HTML}}')
REGENERATE = True

# TODO: hack
if os.path.exists('palette.json'):
    _root = os.getcwd()
else:
    _root = os.path.abspath(os.path.dirname(__file__))


_template_loader = jinja2.FileSystemLoader(searchpath=_root)
_template_env = jinja2.Environment(loader=_template_loader)
_palette = json.load(open(os.path.join(_root, 'palette.json')))


def generate_slide(text, template_file, out_file=None, gen_html=False):
    text = markdown2.markdown(
        text, extras=['break-on-newline', 'fenced-code-blocks'])
    print(text)

    if out_file is None:
        out_file = slugify(text) + '.png'

    template = _template_env.get_template(template_file)
    # this is where to put args to the template renderer
    html = template.render({
        'text': text,
        'palette': _palette
    })

    if gen_html:
        html_file_name = out_file + '.html'
        with open(html_file_name, 'w', encoding='utf-8') as f:
            f.write(html)
        # webbrowser.open(html_file_name)

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
            await page.screenshot({'path': out_file, 'omitBackground': True})
            await browser.close()

        asyncio.get_event_loop().run_until_complete(main())


if __name__ == '__main__':
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

    for text in slides:
        out_file = os.path.join(out_folder, slugify(text) + '.png')
        if REGENERATE or (not os.path.exists(out_file)):
            print2('Generate %s ...' % out_file)

            generate_slide(text,
                           template_file,
                           out_file=out_file,
                           gen_html=GEN_HTML)
