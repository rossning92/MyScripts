from _shutil import *


def download_bili(url):
    retry = 3
    while retry > 0:
        try:
            with open("/tmp/cookie.json") as f:
                data = json.load(f)

            cookie = "; ".join(["%s=%s" % (x["name"], x["value"]) for x in data])
            call_echo(["annie", "-p", "-c", cookie, url], shell=False)
            return
        except subprocess.CalledProcessError:
            print2("on error, retrying...")
            retry -= 1


if __name__ == "__main__":
    if len(sys.argv) == 2:
        url = sys.argv[1]
        cd("~/Desktop/Bilibili", auto_create_dir=True)
        download_bili(url)
    else:
        raise Exception("invalid parameter: url")

