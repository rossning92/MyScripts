import subprocess
import os


def generate_video_matrix(vid_files, titles=None, out_file=None, columns=None, fps=None, crop_rect=None):
    os.environ['IMAGEMAGICK_BINARY'] = r"C:\Program Files\ImageMagick-7.0.8-Q16\magick.exe"
    try:
        import moviepy
    except:
        subprocess.call('pip install moviepy')

    from moviepy.editor import VideoFileClip, TextClip, ColorClip, clips_array, vfx
    import numpy as np
    from moviepy.video.fx.all import crop

    if out_file is None:
        out_file = 'combined.mp4'

    if type(vid_files[0]) == str:
        vid_clips = [VideoFileClip(x, resize_algorithm='fast_bilinear') for x in vid_files]
    else:
        vid_clips = vid_files
    max_h = np.max([x.h for x in vid_clips])

    vid_clips = [x.fx(vfx.resize, max_h / x.h) for x in vid_clips]
    if crop_rect:
        vid_clips = [crop(x,
                          x1=crop_rect[0],
                          y1=crop_rect[1],
                          width=crop_rect[2],
                          height=crop_rect[3]) for x in vid_clips]

    vid_clips = [v.margin(2) for v in vid_clips]

    min_duration = np.min([v.duration for v in vid_clips])
    print('Set duration to min of all videos: %i' % min_duration)
    vid_clips = [v.set_duration(min_duration) for v in vid_clips]

    def create_text_clip(text, dura):
        global src
        return TextClip(text,
                        font='Verdana',
                        fontsize=max_h / 20,
                        color='white') \
            .set_duration(dura)

    if titles is None:
        titles = [os.path.splitext(os.path.basename(x))[0] for x in vid_files]
    text_clips = [create_text_clip(x, min_duration) for x in titles]

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

    final.write_videofile(out_file, fps=fps)


def make_video(images, fps=30, out_file='output.mp4', format='bgr24'):
    ps = None

    for im in images:
        if not ps:  # Initialize
            w = im.shape[1]
            h = im.shape[0]
            command = [
                'ffmpeg',
                '-y',  # (optional) overwrite output file if it exists
                '-f', 'rawvideo',
                # '-vcodec', 'rawvideo',
                '-s', f'{w}x{h}',  # size of one frame
                '-pix_fmt', format]

            if fps and fps > 0:
                command += ['-r', str(fps)]

            command += [
                '-i', '-',  # The imput comes from a pipe
                '-an',  # Tells FFMPEG not to expect any audio

                # '-vcodec', 'rawvideo',
                # '-vcodec', 'huffyuv',
                # '-c:v', 'libx264', '-preset', 'slow', '-crf', '0',
                '-c:v', 'h264_nvenc', '-profile', 'high444p', '-pixel_format', 'yuv444p', '-preset', 'default',
                # '-hwaccel', 'cuvid',
                # '-vf','scale=-2:720',
                out_file
            ]

            ps = subprocess.Popen(command, stdin=subprocess.PIPE)

        ps.stdin.write(im.tostring())

    ps.stdin.close()


def ffmpeg(in_file, out_file='out.mp4', start_and_duration=None, reencode=False, nvenc=True, extra_args=None):
    args = ['ffmpeg',
            '-i', in_file]

    if start_and_duration:
        args += ['-ss', str(start_and_duration[0]),
                 '-strict', '-2',
                 '-t', str(start_and_duration[1])]

    if extra_args:
        args += extra_args

    if reencode:
        if nvenc:
            args += ['-c:v', 'h264_nvenc', '-preset', 'slow', '-qp', '19']
        else:
            args += ['-c:v', 'libx264', '-preset', 'slow', '-crf', '22']

        args += ['-c:a', 'aac', '-b:a', '128k']  # Audio

    args += [out_file, '-y']  # Override file

    subprocess.check_call(args)


def extract_imgs(f, fps=1, out_folder='out'):
    os.makedirs(out_folder, exist_ok=True)

    subprocess.check_call([
        'ffmpeg',
        '-hwaccel', 'cuvid',
        # '-ss', '50',
        '-i', f,
        '-an',
        # '-vf', f'fps=1/60',
        # '-vf', "select='not(mod(n,800))'",
        '-vf', "select='eq(pict_type,PICT_TYPE_I)'",
        # '-vframes:v', '1',
        '-vsync', 'vfr',
        '-qscale:v', '2',
        os.path.join(out_folder, "%04d.jpg"),
    ])
