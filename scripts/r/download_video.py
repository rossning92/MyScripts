import os
import subprocess
import sys

from _shutil import call_echo, print2
from _script import get_variable

root = os.path.dirname(os.path.realpath(__file__))


def get_default_download_dir(name):
    d = get_variable("VIDEO_DOWNLOAD_DIR")
    if not d:
        d = os.path.join(os.path.expanduser("~"), "Desktop")
    d = os.path.join(d, name)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def download_bilibili(url, download_dir=None):
    # Cookie
    kvp = []
    with open(os.path.expanduser("~/bilibili-cookies.txt")) as f:
        lines = f.read().splitlines()
        for line in lines:
            if line.startswith("#"):
                continue
            if line.strip() == "":
                continue
            cols = line.split("\t")
            kvp.append(cols[-2] + "=" + cols[-1])
    cookie = "; ".join(kvp)

    call_echo(["lux", "-p", "-c", cookie, url], shell=False, cwd=download_dir)


def download_youtube(url, download_dir=None):
    call_echo(
        ["yt-dlp", "-f", "bestvideo+bestaudio", "--no-mtime", url], cwd=download_dir
    )


def download_video(url):
    retry = 3
    while retry > 0:
        try:
            if "bilibili" in url:
                download_bilibili(
                    url, download_dir=get_default_download_dir("Bilibili"),
                )
            elif "youtube" in url:
                download_youtube(
                    url, download_dir=get_default_download_dir("Youtube"),
                )
            return
        except subprocess.CalledProcessError:
            print2("on error, retrying...")
            retry -= 1


if __name__ == "__main__":
    if len(sys.argv) == 2:
        url = sys.argv[1]
        download_video(url)
    else:
        raise Exception("invalid parameter: url")
