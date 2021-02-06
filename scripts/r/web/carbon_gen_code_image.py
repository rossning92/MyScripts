from _shutil import *

IMG_SIZE = (1920, 1080)
BORDER = 2


def gen_code_image(code, out_file, line_no=True):
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

    # HACK: add space before each line
    code = "\n".join(["  %s" % x for x in code.splitlines()])

    tmp_file = write_temp_file(code, ".py")

    call2(f"carbon-now {tmp_file} -t {os.path.splitext(out_file)[0]}")

    from PIL import Image, ImageDraw

    im2 = Image.open(out_file)
    im2 = im2.crop((BORDER, BORDER, im2.width - 2 * BORDER, im2.height - 2 * BORDER))

    top_left = (
        (IMG_SIZE[0] - im2.width) // 2 + BORDER,
        (IMG_SIZE[1] - im2.height) // 2 + BORDER,
    )
    print(top_left)

    im = Image.new("RGB", IMG_SIZE)

    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, IMG_SIZE[0], IMG_SIZE[1]), fill=0xC1B7AD)
    del draw

    im.paste(im2, top_left)

    # write to stdout
    im.save(out_file)


setup_nodejs(install=True)

try:
    call2("carbon-now --version")
except:
    call2("yarn global add carbon-now-cli")

if __name__ == "__main__":
    file = get_files(cd=True)[0]
    s = open(file, encoding="utf-8").read()

    out_file = os.path.splitext(file)[0] + ".png"
    gen_code_image(s, out_file)
    call2(f"start {out_file}")
