from _shutil import *

IMG_SIZE = (1920, 1080)
BORDER = 2

CONFIG = '''

'''

setup_nodejs(install=True)

with open(expanduser('~/.carbon-now.json'), 'w') as f:
    json.dump({
        "latest-preset": {
            "t": "3024-night",
            "bg": "#ADB7C1",
            "wt": "none",
            "wc": True,
            "fm": "Hack",
            "fs": "18px",
            "ln": False,
            "ds": True,
            "dsyoff": "3px",
            "dsblur": "50px",
            "wa": True,
            "lh": "133%",
            "pv": "100px",
            "ph": "100px",
            "si": False,
            "wm": False,
            "es": "4x",
            "type": "png"
        }
    }, f)

f = get_files(cd=True)[0]
name = os.path.splitext(f)[0]

try:
    call2(f'carbon-now {f} -t {name}')
except:
    print2('Please re-run...', color='red')
    call2('npm i -g carbon-now-cli')
    exit(0)

from PIL import Image, ImageDraw

im2 = Image.open(name + '.png')
im2 = im2.crop((BORDER,
                BORDER,
                im2.width - 2 * BORDER,
                im2.height - 2 * BORDER))

top_left = ((IMG_SIZE[0] - im2.width) // 2 + BORDER,
            (IMG_SIZE[1] - im2.height) // 2 + BORDER)
print(top_left)

im = Image.new('RGB', IMG_SIZE)

draw = ImageDraw.Draw(im)
draw.rectangle((0, 0, IMG_SIZE[0], IMG_SIZE[1]), fill=0xC1B7AD)
del draw

im.paste(im2, top_left)

# write to stdout
im.save(f'{name}.png')
call2(f'start {name}.png')
