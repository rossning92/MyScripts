from _shutil import *

IMG_SIZE = (1920, 1080)
BORDER = 2

setup_nodejs(install=True)


def gen_image(code, out_file):
    with open(expanduser("~/.carbon-now.json"), "w") as f:
        json.dump(
            {
                "latest-preset": {
                    "t": "3024-night",
                    "bg": "#ADB7C1",
                    "wt": "none",
                    "wc": False,  # window controls
                    "fm": "Hack",
                    "fs": "14px",
                    "ln": True,  # line no
                    "ds": True,  # drop shadow
                    "dsyoff": "3px",
                    "dsblur": "50px",
                    "wa": False,  # width adjustment
                    "lh": "133%",
                    "pv": "100px",
                    "ph": "100px",
                    "si": True,  # Squared image
                    "wm": False,  # Watermark
                    "es": "2x",
                    "type": "png",
                }
            },
            f,
        )

    tmp_file = write_temp_file(code, ".txt")

    try:
        call2(f"carbon-now {tmp_file} -t {os.path.splitext(out_file)[0]}")
    except:
        print2("Please re-run...", color="red")
        call2("yarn global add carbon-now-cli")
        exit(0)

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
    # call2(f"start {out_file}.png")


if __name__ == "__main__":
    file = get_files(cd=True)[0]
    s = open(file, encoding="utf-8").read()

    out_file = os.path.splitext(file)[0] + ".png"
    gen_image(s, out_file)
