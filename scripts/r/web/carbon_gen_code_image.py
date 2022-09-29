from _shutil import *

IMG_SIZE = (1920, 1080)
BORDER = 2


def gen_code_image(file, out_file, line_no=True):
    with open(expanduser("~/.carbon-now.json"), "w") as f:
        json.dump(
            {
                "latest-preset": {
                    "t": "vscode",
                    "bg": "#ADB7C1",
                    "wt": "none",  # Window theme
                    "wc": True,  # Window controls
                    "fm": "Hack",
                    "fs": "24px",
                    "ln": line_no,  # Line no
                    "ds": True,  # Drop shadow
                    "dsyoff": "0px",
                    "dsblur": "10px",
                    "wa": False,  # Width adjustment
                    "lh": "133%",
                    "pv": "100px",  # Vertical padding
                    "ph": "100px",  # Horizonatal padding
                    "si": True,  # Squared image
                    "wm": False,  # Watermark
                    "es": "2x",
                    "type": "png",
                }
            },
            f,
        )

    call2(f"carbon-now {file} -t {os.path.splitext(out_file)[0]}")


setup_nodejs(install=True)

try:
    call2("carbon-now --version")
except:
    call2("yarn global add carbon-now-cli")

if __name__ == "__main__":
    file = get_files(cd=True)[0]
    out_file = os.path.splitext(file)[0] + ".png"

    gen_code_image(file, out_file)

    # call2(f"start {out_file}")
