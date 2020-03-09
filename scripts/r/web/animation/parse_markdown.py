from _shutil import *
import generate_slides
import urllib
import webbrowser
import capture_animation


def get_meta_data(type_):
    s = open(f, 'r', encoding='utf-8').read()
    matches = re.findall('<!-- ' + type_ + r'([\w\W]+?)-->', s)
    matches = [x.strip() for x in matches]
    return matches


f = r'{{MD_FILE}}'
OUT_DIR = r'{{OUT_DIR}}'


cd(OUT_DIR)


# for text in get_meta_data('slide:'):
#     generate_slides.generate_slide(text=text,
#                                    template_file='text.html',
#                                    gen_html=True)


for s in get_meta_data('ani:'):
    out_file = slugify('ani-' + s) + '.mov'
    if not os.path.exists(out_file):
        url = 'http://localhost:8080/%s.html' % s
        capture_animation.capture_js_animation(
            url,
            out_file=out_file
        )


for s in get_meta_data('title-animation:'):
    out_file = slugify('title-animation-' + s) + '.mov'

    if not os.path.exists(out_file):
        h1 = re.search('^# (.*)', s, flags=re.MULTILINE).group(1)
        h2 = re.search('^## (.*)', s, flags=re.MULTILINE).group(1)
        url = 'http://localhost:8080/title-animation.html?h1=%s&h2=%s' % (
            urllib.parse.quote(h1),
            urllib.parse.quote(h2)
        )
        capture_animation.capture_js_animation(
            url,
            out_file=out_file)


for s in get_meta_data('list-animation:'):
    out_file = slugify('list-animation-' + s) + '.mov'

    if not os.path.exists(out_file):
        url = 'http://localhost:8080/list-animation.html?s=%s' % (
            urllib.parse.quote(s)
        )
        capture_animation.capture_js_animation(
            url,
            out_file=out_file)
