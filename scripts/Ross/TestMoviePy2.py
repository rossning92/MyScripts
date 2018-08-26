from moviepy.editor import *
import moviepy.video.fx as vfx
import numpy as np
import os

DURATION = 3

desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')

clip1 = VideoFileClip(r"C:\Users\Ross\Desktop\Lecture 5 _ Convolutional Neural Networks-bNb2fEVKeEo.mkv")
clip2 = VideoFileClip(r"C:\Users\Ross\Desktop\Lecture 9 _ CNN Architectures-DAOcjicFr1Y.mkv")

clip_left = clip1 \
    .fx(vfx.all.crop, x1=0, y1=0, x2=clip1.w // 2, y2=clip1.h) \
    .subclip(0)

clip_right = clip2 \
    .fx(vfx.all.crop, x1=0, y1=0, x2=clip1.w // 2, y2=clip1.h) \
    .subclip(1)


def create_text(text, i):
    return TextClip(text,
                    font='Verdana',
                    fontsize=40,
                    color='green') \
        .set_duration(DURATION)


text_left = create_text("AAA", 0)
text_right = create_text("BBB", 1)

final = clips_array([
    [clip_left, clip_right],
    [text_left, text_right]
]).set_duration(DURATION)


def draw_line(im):
    cx = im.shape[1] // 2
    im[:, cx - 1: cx + 1] = [0, 255, 0]
    return im


final = final.fl_image(draw_line)
# final = final.resize(0.5)

final.show(interactive=True)
final.write_videofile(os.path.join(desktop, 'output.mp4'))
# final.write_gif(os.path.join(desktop, 'output.gif'), fuzz=10)
