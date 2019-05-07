from moviepy.editor import *
import moviepy.video.fx as vfx
import numpy as np

clip = VideoFileClip(r"C:\Users\Ross\Desktop\output_1.mp4")

smallClip = vfx.all.crop(clip, x1=50, y1=60, x2=460, y2=275)

video = CompositeVideoClip([
    smallClip,
    smallClip.set_pos(smallClip.size),
    TextClip("My Holidays 2013", font='Verdana', fontsize=80, color='yellow', stroke_color='gray').set_pos('center').set_duration(smallClip.duration)
], size=np.array(smallClip.size) * 2)

video.write_videofile("out.mp4")

