import argparse
import os
import shutil
import subprocess
import sys

from _script import get_variable
from _shutil import call_echo, get_home_path, print2

root = os.path.dirname(os.path.realpath(__file__))


def get_download_dir(name, base=None):
    if base is None:
        d = get_variable("VIDEO_DOWNLOAD_DIR")
        if not d:
            d = os.path.join(os.path.expanduser("~"), "Desktop")
    else:
        d = base
    d = os.path.join(d, name)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def download_bilibili(url, download_dir=None):
    # Cookie
    kvp = []
    with open(os.path.join(get_home_path(), "bilibili-cookies.txt")) as f:
        lines = f.read().splitlines()
        for line in lines:
            if line.startswith("#"):
                continue
            if line.strip() == "":
                continue
            cols = line.split("\t")
            kvp.append(cols[-2] + "=" + cols[-1])
    cookie = ";".join(kvp)

    call_echo(["lux", "-c", cookie, url], shell=False, cwd=download_dir)


def download_youtube(url, download_dir=None, audio_only=False, download_playlist=False):
    if not shutil.which("yt-dlp"):
        call_echo([sys.executable, "-m", "pip", "install", "-U", "yt-dlp", "--user"])

    if audio_only:
        format = "bestaudio"
    else:
        format = "bestvideo+bestaudio"
    args = ["yt-dlp", "-f", format, "--no-mtime", url]
    if not download_playlist:
        args.append("--no-playlist")
    call_echo(args, cwd=download_dir)


def download_video(url, audio_only, download_dir=None):
    retry = 3
    while retry > 0:
        try:
            if "bilibili" in url:
                download_bilibili(
                    url, download_dir=get_download_dir("Bilibili", base=download_dir)
                )
            elif "youtube" in url:
                download_youtube(
                    url,
                    download_dir=get_download_dir("Youtube", base=download_dir),
                    audio_only=audio_only,
                )
            return
        except subprocess.CalledProcessError:
            print2("on error, retrying...")
            retry -= 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_only", default=False, action="store_true")
    parser.add_argument("--download_dir", default=None, type=str)
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    download_video(
        url=args.url, audio_only=args.audio_only, download_dir=args.download_dir
    )
