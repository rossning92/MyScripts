import glob
import os
import subprocess

from _shutil import download, remove, start_process, unzip

INSTALL_DIR = r"C:\Tools\RenderDoc"

os.chdir(os.path.join(os.environ["USERPROFILE"], "Downloads"))


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

    f = download(url)
    print(f)

    # remove(INSTALL_DIR)
    unzip(f, INSTALL_DIR)


def start_renderdoc(version=None):
    match = glob.glob(
        os.path.join(
            INSTALL_DIR, "**" if version is None else f"*{version}*", "qrenderdoc.exe"
        ),
        recursive=True,
    )
    if not match:
        return False

    start_process(match[0])

    return True


if __name__ == "__main__":
    if not start_renderdoc("{{_VERSION}}"):
        install_renderdoc("{{_VERSION}}")
