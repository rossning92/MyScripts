from _shutil import *
import generate_slides
import urllib
import webbrowser
import capture_js_animation

f = r'C:\Users\Ross\Google Drive\Notes\Kidslogic\Coding_in_3_minutes\ep13\ep13.md'


def get_meta_data(type_):
    s = open(f, 'r', encoding='utf-8').read()
    matches = re.findall('<!-- ' + type_ + r'([\w\W]+?)-->', s)
    matches = [x.strip() for x in matches]
    return matches


cd(os.path.dirname(f))


for text in get_meta_data('slide'):
    generate_slides.generate_slide(text=text,
                                   template_file='text.html',
                                   gen_html=True)


for text in get_meta_data('title'):
    h1 = re.search('^# (.*)', text, flags=re.MULTILINE).group(1)
    h2 = re.search('^## (.*)', text, flags=re.MULTILINE).group(1)

    url = 'http://localhost:8080/title.html?h1=%s&h2=%s' % (
        urllib.parse.quote(h1),
        urllib.parse.quote(h2)
    )
    capture_js_animation.capture_js_animation(
        url,
        out_file=slugify(text) + '.mov'
    )
    # webbrowser.open(url)
