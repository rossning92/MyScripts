from _shutil import *
from r.open_with.open_with_ import open_with

setup_nodejs()


def convert_md_to_pdf(f):
    try:
        call2('mdpdf --version')
    except:
        call_echo('yarn global add mdpdf')

    call_echo('mdpdf --format=A5 --border-top=1mm --border-bottom=1mm "%s"' % f)

    open_with(os.path.splitext(f)[0] + '.pdf')


if __name__ == '__main__':
    if r'{{MD_FILE}}':
        f = r'{{MD_FILE}}'
    else:
        f = get_files()[0]
    convert_md_to_pdf(f)
