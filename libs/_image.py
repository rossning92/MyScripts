from PIL import Image, ImageDraw, ImageFont
import glob
import os
import math
import re


def crop_image_file(file_name, rect=None, rect_normalized=None):
    im = Image.open(file_name)
    im = crop_image(im, rect, rect_normalized)
    im.save(file_name)


def crop_image(im, rect=None, rect_normalized=None):
    import numpy as np
    if type(im) == np.ndarray:
        h, w = im.shape[0:2]
    else:
        w, h = im.width, im.height

    if rect_normalized:
        rect = [
            rect_normalized[0] * w,
            rect_normalized[1] * h,
            rect_normalized[2] * w,
            rect_normalized[3] * h
        ]
        rect = [int(x) for x in rect]

    if type(im) == np.ndarray:
        im = im[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
    else:
        im = im.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))

    return im


def scale_image(im, sx, sy):
    return im.resize((int(sx * im.size[0]), int(sy * im.size[1])), Image.ANTIALIAS)


def show_im(*imgs, format='rgb', out_image_name=None):
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(len(imgs), 1))
    for i, im in enumerate(imgs):
        if len(im.shape) == 3 and im.shape[2] == 3 and format == 'bgr':
            im = im[..., ::-1]

        # Visualize two channel image (e.g. optical flow, vector)
        if len(im.shape) == 3 and im.shape[2] == 2:
            import cv2
            import numpy as np

            hsv = np.zeros([im.shape[0], im.shape[1], 3])
            hsv[..., 1] = 255
            mag, ang = cv2.cartToPolar(im[..., 0], im[..., 1])
            hsv[..., 0] = ang * 180 / np.pi / 2
            hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
            hsv = hsv.astype(np.uint8)
            im = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        fig.add_subplot(1, len(imgs), i + 1)
        plt.imshow(im)

    if out_image_name:
        plt.savefig(out_image_name, dpi=200)
    else:
        plt.show()

    plt.close(fig)


def draw_text(im, text, box, text_outline=2, font_color='white', align='center', font_scale=1.0):
    PADDING = 4

    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("arial.ttf", int(box[3] / 16 * font_scale))
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

    draw.multiline_text((x - text_outline, y), text, font=font, fill="black", align='center')
    draw.multiline_text((x + text_outline, y), text, font=font, fill="black", align='center')
    draw.multiline_text((x, y - text_outline), text, font=font, fill="black", align='center')
    draw.multiline_text((x, y + text_outline), text, font=font, fill="black", align='center')
    draw.multiline_text((x, y), text, font=font, fill=font_color, align='center')

    del draw


def combine_images(image_files=None, images=None, out_file=None, parse_file_name=None, cols=4, spacing=4, scale=1.0,
                   text_outline=2,
                   gif_duration=500, generate_atlas=True, generate_gif=True, draw_label=True, labels=None,
                   label_align='center',
                   font_color='white', title=None,
                   title_color='white',
                   col_major_order=False,
                   font_scale=1.0):
    file_list = None
    if image_files:
        if type(image_files) == list:
            file_list = image_files
        else:
            file_list = glob.glob(image_files)

        if len(file_list) == 0:
            raise Exception('No image files has been found: %s' % image_files)

        imgs = [Image.open(f) for f in file_list]
        if scale != 1.0:
            imgs = [im.resize((int(im.width * scale), int(im.height * scale)), Image.NEAREST) for im in imgs]

    elif images:
        # Convert to PIL image
        imgs = [Image.fromarray(x, 'RGB') for x in images]

    else:
        raise Exception("`image_files` and `images` cannot be None at the same time.")

    # Adjust column size if it's smaller than the number of files
    if len(imgs) < cols:
        cols = len(imgs)

    # Add text
    if draw_label:
        for i in range(len(imgs)):
            im = imgs[i]

            if labels is not None:
                text = labels[i]
            elif file_list is not None:
                text = os.path.splitext(os.path.basename(file_list[i]))[0]
                if parse_file_name is not None:
                    text = parse_file_name(text)
                else:
                    text = text.replace('_', ' ')
            else:
                draw_label = False

            if draw_label:
                draw_text(im, text, (0, 0, imgs[0].width, imgs[0].height), text_outline, font_color,
                          align=label_align, font_scale=font_scale)

    if generate_atlas:
        num_imgs = len(imgs)
        rows = int(math.ceil(num_imgs / cols))
        if col_major_order:  # Swap rows and cols
            t = rows
            rows = cols
            cols = t

        im_combined = Image.new('RGB',
                                (imgs[0].width * cols + spacing * (cols - 1),
                                 imgs[0].height * rows + spacing * (rows - 1)))

        for c in range(len(imgs)):
            if not col_major_order:
                i = c // cols
                j = c % cols
            else:
                j = c // rows
                i = c % rows

            x = j * imgs[0].width + j * spacing
            y = i * imgs[0].height + i * spacing
            im_combined.paste(imgs[c], (x, y))
            c += 1

        if title is not None:
            draw_text(im_combined,
                      title,
                      (0, 0, im_combined.width, im_combined.height),
                      text_outline,
                      title_color,
                      align='topLeft',
                      font_scale=font_scale)

    if out_file:
        out_file = os.path.splitext(out_file)[0]  # Remove file extension
        dir_name = os.path.dirname(out_file)
        if dir_name:
            os.makedirs(os.path.dirname(out_file), exist_ok=True)

        if generate_atlas:
            im_combined.save(out_file + '.png')

        if generate_gif:
            imgs[0].save(out_file + '.gif',
                         save_all=True,
                         append_images=imgs[1:],
                         duration=gif_duration,
                         quality=100,
                         loop=0)  # Repeat forever

    import numpy
    return numpy.array(im_combined)


def parse_file_name(s):
    gain_x = re.findall('GainX\((.*?)\)', s)[0].replace('.00', '')
    gain_y = re.findall('GainY\((.*?)\)', s)[0].replace('.00', '')
    s = 'GainX: %s\nGainY: %s' % (gain_x, gain_y)
    return s


def select_region(image_file):
    import cv2
    im = cv2.imread(image_file)

    # Select ROI
    box = cv2.selectROI(im)
    return box
