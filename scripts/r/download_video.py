import argparse
import logging
import os
import re

import requests
from _shutil import (
    call_echo,
    get_home_path,
    get_newest_file,
    prepend_to_path,
    setup_logger,
)
from utils.retry import retry

root = os.path.dirname(os.path.realpath(__file__))


def get_download_dir(name, base=None):
    if base is None:
        d = os.environ["VIDEO_DOWNLOAD_DIR"]
        if not d:
            d = os.path.join(os.path.expanduser("~"), "Desktop")
    else:
        d = base
    d = os.path.join(d, name)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def get_redirected_url(url):
    return requests.get(url).url


def download_bilibili(url, download_dir=None):
    prepend_to_path([os.path.join(get_home_path(), "go", "bin")])
    cookie_file = os.path.join(get_home_path(), ".bilibili-cookies.txt")
    with open(cookie_file, "r") as f:
        cookie = f.read()
    call_echo(["lux", "-c", cookie, url], shell=False, cwd=download_dir)
    # call_echo(["BBDown", "-c", cookie, url], shell=False, cwd=download_dir)


def download_youtube(url, download_dir=None, audio_only=False, download_playlist=False):
    if audio_only:
        format = "bestaudio"
    else:
        format = "bestvideo+bestaudio"
    args = ["yt-dlp", "-f", format, "--no-mtime", url]
    if not download_playlist:
        args.append("--no-playlist")
    call_echo(args, cwd=download_dir)


@retry()
def download_video(url, audio_only=False, download_dir=None, save_url=True):
    url = get_redirected_url(url)
    if "bilibili.com" in url:
        ddir = get_download_dir("Bilibili", base=download_dir)
        download_bilibili(
            url,
            download_dir=ddir,
        )
    elif "youtube.com" in url:
        ddir = get_download_dir("Youtube", base=download_dir)
        download_youtube(
            url,
            download_dir=ddir,
            audio_only=audio_only,
        )

    # Save url
    if save_url:
        # Remove anything after "&":
        # https://www.youtube.com/watch?v=xxxxxxxx&list=yyyyyyyy&start_radio=1
        url = re.sub(r"(\?(?!v)|&).*$", "", url)
        url_file = get_newest_file(os.path.join(ddir, "*.*")) + ".url"
        logging.info("Save url to: %s" % url_file)
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_only", default=False, action="store_true")
    parser.add_argument("--download_dir", default=None, type=str)
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    setup_logger()

    download_video(
        url=args.url, audio_only=args.audio_only, download_dir=args.download_dir
    )
