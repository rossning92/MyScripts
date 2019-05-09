from PIL import Image, ImageDraw, ImageFont
import glob
import os
import math
import re


def _draw_centered_text(im, text, box, text_outline, font_color, align='center'):
    PADDING = 4

    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("arial.ttf", box[3] // 16)
    w, h = draw.multiline_textsize(text, font=font)

    if align == 'top':
        x = box[0] + (box[2] - w) / 2
        y = box[1] + PADDING
    elif align == 'topLeft':
        x = box[0] + PADDING
        y = box[1] + PADDING
    else:  # center
        x = box[0] + (box[2] - w) / 2
        y = box[1] + (box[3] - h) / 2

    draw.multiline_text((x - text_outline, y), text, font=font, fill="black")
    draw.multiline_text((x + text_outline, y), text, font=font, fill="black")
    draw.multiline_text((x, y - text_outline), text, font=font, fill="black")
    draw.multiline_text((x, y + text_outline), text, font=font, fill="black")
    draw.multiline_text((x, y), text, font=font, fill=font_color)

    del draw


def combine_images(image_files, out_file, parse_file_name=None, cols=4, spacing=4, scale=1.0, text_outline=2,
                   gif_duration=500, generate_atlas=True, draw_label=True, labels=None, label_align='center', font_color='white', title=None,
                   title_color='white'):
    out_file = os.path.splitext(out_file)[0]  # Remove file extension

    if type(image_files) == list:
        file_list = image_files
    else:
        file_list = glob.glob(image_files)

    if len(file_list) == 0:
        raise Exception('No image files has been found: %s' % image_files)

    # Adjust column size if it's smaller than the number of files
    if len(file_list) < cols:
        cols = len(file_list)

    imgs = [Image.open(f) for f in file_list]
    if scale != 1.0:
        imgs = [im.resize((int(im.width * scale), int(im.height * scale)), Image.NEAREST) for im in imgs]

    # Add text
    if draw_label:
        for i in range(len(imgs)):
            im = imgs[i]
            text = os.path.splitext(os.path.basename(file_list[i]))[0]
            if parse_file_name is not None:
                text = parse_file_name(text)
            elif labels is not None:
                text = labels[i]
            _draw_centered_text(im, text, (0, 0, imgs[0].width, imgs[0].height), text_outline, font_color, align=label_align)

    if generate_atlas:
        num_imgs = len(imgs)
        rows = int(math.ceil(num_imgs / cols))
        im_combined = Image.new('RGB',
                                (imgs[0].width * cols + spacing * (cols - 1),
                                 imgs[0].height * rows + spacing * (rows - 1)))
        c = 0
        for m in range(len(imgs)):
            i = c // cols
            j = c % cols
            x = j * imgs[0].width + j * spacing
            y = i * imgs[0].height + i * spacing
            im_combined.paste(imgs[m], (x, y))
            c += 1

        dir_name = os.path.dirname(out_file)
        if dir_name:
            os.makedirs(os.path.dirname(out_file), exist_ok=True)

        if title is not None:
            _draw_centered_text(im_combined,
                                title,
                                (0, 0, im_combined.width, im_combined.height),
                                text_outline,
                                title_color,
                                align='topLeft')
        im_combined.save(out_file + '.png')

    imgs[0].save(out_file + '.gif',
                 save_all=True,
                 append_images=imgs[1:],
                 duration=gif_duration,
                 quality=100,
                 loop=0)  # Repeat forever


def parse_file_name(s):
    gain_x = re.findall('GainX\((.*?)\)', s)[0].replace('.00', '')
    gain_y = re.findall('GainY\((.*?)\)', s)[0].replace('.00', '')
    s = 'GainX: %s\nGainY: %s' % (gain_x, gain_y)
    return s
