import os
import subprocess

from _shutil import call_echo, get_files, setup_nodejs

from open_with.open_with import open_with


def convert_md_to_pdf(f, page_size="A5"):
    try:
        subprocess.check_call(["mdpdf", "--version"])
    except:
        call_echo("yarn global add mdpdf")

    call_echo(f'mdpdf --format={page_size} --border-top=1mm --border-bottom=1mm "{f}"')

    open_with(os.path.splitext(f)[0] + ".pdf")


if __name__ == "__main__":
    setup_nodejs()

    if r"{{MD_FILE}}":
        f = r"{{MD_FILE}}"
    else:
        f = get_files()[0]
    convert_md_to_pdf(f)
