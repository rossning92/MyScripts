import glob
import os
import subprocess
import sys

from _shutil import get_temp_file_name


def generate_video_matrix(
    vid_files, titles=None, out_file=None, columns=None, fps=None, crop_rect=None
):
    os.environ["IMAGEMAGICK_BINARY"] = glob.glob(
        r"C:\Program Files\ImageMagick-*\magick.exe"
    )[0]
    try:
        import moviepy
    except:
        subprocess.call("pip install moviepy")

    import numpy as np
    from moviepy.editor import ColorClip, TextClip, VideoFileClip, clips_array, vfx
    from moviepy.video.fx.all import crop

    if out_file is None:
        out_file = "combined.mp4"

    if type(vid_files[0]) == str:
        vid_clips = [
            VideoFileClip(x, resize_algorithm="fast_bilinear") for x in vid_files
        ]
    else:
        vid_clips = vid_files
    max_h = np.max([x.h for x in vid_clips])

    vid_clips = [x.fx(vfx.resize, max_h / x.h) for x in vid_clips]
    if crop_rect:
        vid_clips = [
            crop(
                x,
                x1=crop_rect[0],
                y1=crop_rect[1],
                width=crop_rect[2],
                height=crop_rect[3],
            )
            for x in vid_clips
        ]

    vid_clips = [v.margin(2) for v in vid_clips]

    min_duration = np.min([v.duration for v in vid_clips])
    print("Set duration to min of all videos: %i" % min_duration)
    vid_clips = [v.set_duration(min_duration) for v in vid_clips]

    def create_text_clip(text, dura):
        global src
        return TextClip(
            text, font="Verdana", fontsize=max_h / 20, color="white"
        ).set_duration(dura)

    if titles:
        text_clips = [create_text_clip(x, min_duration) for x in titles]

    arr = []
    if columns is not None:
        for i in range(0, len(vid_clips), columns):
            arr.append(vid_clips[i : i + columns])
            if titles:
                arr.append(text_clips[i : i + columns])

        remainder = len(vid_clips) % columns
        if remainder != 0:
            remainder = columns - remainder
            blank_clip = ColorClip((1, 1), color=(0, 0, 0), duration=0)
            arr[-1].extend([blank_clip] * remainder)
            arr[-2].extend([blank_clip] * remainder)

    else:
        arr.append(vid_clips)
        if titles:
            arr.append(text_clips)

    final = clips_array(arr)

    final.write_videofile(out_file, fps=fps)


def make_video(images, fps=30, out_file="output.mp4", format="bgr24"):
    ps = None

    for im in images:
        if not ps:  # Initialize
            w = im.shape[1]
            h = im.shape[0]
            command = [
                "ffmpeg",
                "-y",  # (optional) overwrite output file if it exists
                "-f",
                "rawvideo",
                # '-vcodec', 'rawvideo',
                "-s",
                f"{w}x{h}",  # size of one frame
                "-pix_fmt",
                format,
            ]

            if fps and fps > 0:
                command += ["-r", str(fps)]

            command += [
                "-i",
                "-",  # The imput comes from a pipe
                "-an",  # Tells FFMPEG not to expect any audio
                # '-vcodec', 'rawvideo',
                # '-vcodec', 'huffyuv',
                # '-c:v', 'libx264', '-preset', 'slow', '-crf', '0',
                "-c:v",
                "h264_nvenc",
                "-profile",
                "high444p",
                "-pixel_format",
                "yuv444p",
                "-preset",
                "default",
                # '-hwaccel', 'cuvid',
                # '-vf','scale=-2:720',
                out_file,
            ]

            ps = subprocess.Popen(command, stdin=subprocess.PIPE)

        ps.stdin.write(im.tostring())

    ps.stdin.close()


def _get_media_duration(f):
    dura = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            f,
        ],
        universal_newlines=True,
    )
    return float(dura)


def ffmpeg(
    in_file,
    out_file=None,
    start_and_duration=None,
    reencode=True,
    nvenc=True,
    extra_args=None,
    quiet=False,
    crf=19,  # visually identical to 0
    preset="slow",
    bitrate=None,
    max_size_mb=None,
    no_audio=False,
    loop=None,
):
    if in_file == out_file:
        overwrite = True
        name, ext = os.path.splitext(in_file)
        out_file = name + ".tmp" + ext
    else:
        overwrite = False

    if out_file is None:
        os.makedirs("out", exist_ok=True)
        out_file = os.path.join(
            os.path.dirname(in_file), "out", os.path.basename(in_file)
        )

    if crf and crf < 19:
        raise Exception("ERROR: 19 is visually identical to 0. Do not go lower.")

    if max_size_mb:
        bitrate = "%.0fk" % (max_size_mb * 8192 / _get_media_duration(in_file))

    args = ["ffmpeg"]

    if loop is not None:
        args += ["-stream_loop", "%d" % loop]

    args += ["-i", in_file]

    if quiet:
        args += ["-hide_banner", "-loglevel", "panic"]

    if start_and_duration:
        args += [
            "-ss",
            str(start_and_duration[0]),
            "-strict",
            "-2",
            "-t",
            str(start_and_duration[1]),
        ]

    if extra_args:
        args += extra_args

    if reencode:
        args += ["-preset", preset]

        if nvenc:
            args += ["-c:v", "h264_nvenc", "-preset", "slow"]

            # https://superuser.com/questions/1236275/how-can-i-use-crf-encoding-with-nvenc-in-ffmpeg/1236387
            # https://gist.github.com/rlan/cc954c891b19c919c939c9b0d2096d35

            args += [
                "-rc:v",
                "vbr_hq",
                "-cq:v",  # 'Constant Quality' mode equivalent to CRF
                "%d" % crf,
                "-b:v",
                "0",
                "-profile:v",
                "main",
            ]
        else:
            args += ["-c:v", "libx264"]
            args += ["-crf", "%d" % crf]

        args += ["-pix_fmt", "yuv420p"]  # Wide used pixel format

        if bitrate:
            args += [
                "-b:v",
                bitrate,
                "-maxrate",
                bitrate,
                "-bufsize",
                bitrate,
            ]

            if 1:
                subprocess.call(
                    args
                    + [
                        "-pass",
                        "1",
                        "-an",
                        "-f",
                        "mp4",
                        "nul" if sys.platform == "win32" else "/dev/null",
                        "-y",
                    ]
                )  # first pass

                args += ["-pass", "2"]

            # args += [
            #     '-maxrate', bitrate,
            #     '-bufsize', bitrate,
            # ]

        if no_audio:
            args += ["-an"]
        else:
            args += ["-c:a", "aac", "-b:a", "128k"]  # Audio

    args += [out_file, "-y"]  # Override file

    print("> " + " ".join(args))
    subprocess.check_call(args)

    if overwrite:
        os.remove(in_file)
        os.rename(out_file, in_file)
        out_file = in_file

    return out_file


def extract_imgs(f, fps=1, out_folder="out"):
    os.makedirs(out_folder, exist_ok=True)

    subprocess.check_call(
        [
            "ffmpeg",
            "-hwaccel",
            "cuvid",
            # '-ss', '50',
            "-i",
            f,
            "-an",
            # '-vf', f'fps=1/60',
            # '-vf', "select='not(mod(n,800))'",
            "-vf",
            "select='eq(pict_type,PICT_TYPE_I)'",
            # '-vframes:v', '1',
            "-vsync",
            "vfr",
            "-qscale:v",
            "2",
            os.path.join(out_folder, "%04d.jpg"),
        ]
    )


def generate_video_preview(in_file, out_file):
    print(out_file)
    subprocess.check_call(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "panic",
            "-ss",
            "10",
            "-i",
            in_file,
            "-vf",
            "scale=w=960:h=540:force_original_aspect_ratio=1,pad=960:540:(ow-iw)/2:(oh-ih)/2",
            # "scale=-2:480",
            "-vframes",
            "1",
            out_file,
        ]
    )
    return out_file


def remove_audio(in_file, out_file=None):
    if out_file is None:
        _, ext = os.path.splitext(in_file)
        out_file = get_temp_file_name(ext)

    subprocess.check_call(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "panic",
            "-i",
            in_file,
            "-c:v",
            "copy",
            "-an",
            out_file,
        ]
    )
    return out_file
