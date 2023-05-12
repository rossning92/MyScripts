import glob
import os
import subprocess

from _shutil import download, start_process, unzip

RENDERDOC_INSTALL_DIR = os.path.expandvars("%APPDATA%\\RenderDoc")


def install_renderdoc(version=None):
    while True:
        try:
            from requests_html import HTMLSession

            break
        except:
            subprocess.call(["python", "-m", "pip", "install", "requests_html"])

    session = HTMLSession()

    r = session.get("https://renderdoc.org/builds")
    if "nightly" in version:
        node = r.html.xpath(
            ".//a[contains(text(),'Nightly') and contains(text(),'ZIP')]"
        )[0]
    else:
        node = r.html.xpath(".//a[contains(text(),'Stable ZIP')]")[0]
    url = node.attrs["href"]

    f = download(url, save_to_tmp=True)
    print(f)

    unzip(f, RENDERDOC_INSTALL_DIR)


def find_renderdoc(version=None):
    match = glob.glob(
        os.path.join(
            RENDERDOC_INSTALL_DIR,
            "**" if version is None else f"*{version}*",
            "qrenderdoc.exe",
        ),
        recursive=True,
    )
    if not match:
        return None
    else:
        return match[0]


def start_renderdoc(version=None):
    rdoc = find_renderdoc(version=version)
    assert rdoc

    start_process(rdoc)

    return True


if __name__ == "__main__":
    version = os.environ.get("_VERSION")
    if not find_renderdoc(version=version):
        install_renderdoc(version=version)
    start_renderdoc(version=version)
