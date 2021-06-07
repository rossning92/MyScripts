from _shutil import *

root = os.path.dirname(os.path.realpath(__file__))


def download_bilibili(url, out_dir=None):
    retry = 3
    while retry > 0:
        try:
            # Cookie
            root = os.path.dirname(os.path.abspath(__file__))
            with open("/tmp/cookie.json") as f:
                data = json.load(f)
            cookie = "; ".join(["%s=%s" % (x["name"], x["value"]) for x in data])

            call_echo(["annie", "-p", "-c", cookie, url], shell=False, cwd=out_dir)
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

