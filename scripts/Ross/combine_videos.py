from moviepy.editor import *
import numpy as np
import os
import glob


def generate_video_matrix(vid_files, captions, out_file='Combined.mp4', columns=None):
    vid_clips = [VideoFileClip(x, resize_algorithm='fast_bilinear') for x in vid_files]
    max_h = np.max([x.h for x in vid_clips])

    vid_clips = [x.fx(vfx.resize, max_h / x.h) for x in vid_clips]
    vid_clips = [x.margin(2) for x in vid_clips]

    dura = np.max([x.duration for x in vid_clips])

    def create_text_clip(text, dura):
        global src
        return TextClip(text,
                        font='Verdana',
                        fontsize=max_h / 20,
                        color='white') \
            .set_duration(dura)

    text_clips = [create_text_clip(x, dura) for x in captions]

    arr = []
    if columns is not None:
        for i in range(0, len(vid_clips), columns):
            arr.append(vid_clips[i:i + columns])
            arr.append(text_clips[i:i + columns])

        remainder = len(vid_clips) % columns
        if remainder != 0:
            remainder = columns - remainder
            blank_clip = ColorClip((1, 1), color=(0, 0, 0), duration=0)
            arr[-1].extend([blank_clip] * remainder)
            arr[-2].extend([blank_clip] * remainder)

    else:
        arr.append(vid_clips)
        arr.append(text_clips)

    final = clips_array(arr)

    final.write_videofile(out_file)


os.chdir(os.environ['CURRENT_FOLDER'])
files = list(glob.glob('*.mp4'))
titles = [os.path.splitext(x)[0] for x in files]

generate_video_matrix(files, titles)
