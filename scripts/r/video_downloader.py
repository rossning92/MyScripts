import os
import subprocess
import sys

from _shutil import call_echo, cd, print2

root = os.path.dirname(os.path.realpath(__file__))


def download_bilibili(url, download_dir=None):
    retry = 3
    while retry > 0:
        try:
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

            call_echo(["annie", "-p", "-c", cookie, url], shell=False, cwd=download_dir)
            return
        except subprocess.CalledProcessError:
            print2("on error, retrying...")
            retry -= 1


if __name__ == "__main__":
    if len(sys.argv) == 2:
        url = sys.argv[1]
        cd("~/Desktop/Bilibili", auto_create_dir=True)
        download_bilibili(url)
        # call_echo("you-get --no-caption --playlist %s" % url)
    else:
        raise Exception("invalid parameter: url")

