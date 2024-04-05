import argparse
import os
from typing import Optional

from _shutil import setup_logger
from _video import ffmpeg, hstack_videos
from open_with.open_with import open_with

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="+")
    args = parser.parse_args()

    setup_logger()

    crop_rect = (
        [int(x) for x in os.environ["_CROP_RECT"].split()[0:4]]
        if os.environ.get("_CROP_RECT")
        else None
    )

    start: Optional[float]
    duration: Optional[float]
    if os.environ.get("_START_AND_DURATION"):
        start_str, duration_str = os.environ["_START_AND_DURATION"].split()
        start = float(start_str)
        duration = float(duration_str)
    else:
        start = None
        duration = None

    for file in args.file:
        if not os.path.isfile(file):
            continue

        out_dir = os.path.join(os.path.dirname(file), "out")
        os.makedirs(out_dir, exist_ok=True)
        name_no_ext = os.path.basename(os.path.splitext(file)[0])
        out_file = os.path.join(out_dir, "%s.mp4" % name_no_ext)

        extra_args = []

        if os.environ.get("_FIND_BEST_CRF"):
            out_files = []
            for crf in [22, 26, 30, 34, 38]:
                extra_args += ["-crf", str(crf)]
                out_files.append(
                    ffmpeg(
                        file,
                        out_file=os.path.join(
                            out_dir, "{}_crf{}.mp4".format(name_no_ext, crf)
                        ),
                        start=0 if start is None else start,
                        duration=5 if duration is None else duration,
                        crf=crf,
                        nvenc=False,
                        title="crf={}".format(crf),
                    )
                )
            out = hstack_videos(out_files)
            open_with(out)

        else:
            env = os.environ
            ffmpeg(
                file,
                out_file=out_file,
                extra_args=extra_args,
                nvenc=bool(env.get("_NVENC")),
                crf=int(env["_CRF"]) if env.get("_CRF") else 19,
                max_size_mb=(
                    float(env["_MAX_SIZE_MB"]) if env.get("_MAX_SIZE_MB") else None
                ),
                start=start,
                duration=duration,
                fps=int(env["_FRAMERATE"]) if env.get("_FRAMERATE") else None,
                width=int(env["_WIDTH"]) if env.get("_WIDTH") else None,
                height=int(env["_HEIGHT"]) if env.get("_HEIGHT") else None,
                no_audio=bool(env.get("_NO_AUDIO")),
                loop=env["_LOOP"] if env.get("_LOOP") else 0,
                crop_rect=crop_rect,
                add_border=env["_ADD_BORDER"] if env.get("_ADD_BORDER") else 0,
                crop_to_1080p=bool(env.get("_CROP_TO_1080P")),
                crop_to_portrait=bool(env.get("_CROP_TO_PORTRAIT")),
                pad_to_1080p=bool(env.get("_PAD_TO_1080P")),
                rotate_ccw=bool(env.get("_ROTATE_CCW")),
                rotate_cw=bool(env.get("_ROTATE_CW")),
                speed=float(env["_SPEED"]) if env.get("_SPEED") else 1,
                title=env.get("_TITLE"),
                to_anamorphic=bool(env.get("_TO_ANAMORPHIC")),
                remove_duplicated_frames=bool(env.get("_REMOVE_DUPLICATED_FRAMES")),
                reverse=bool(env.get("_REVERSE")),
            )

        if env.get("_OPEN") and len(args.file) == 1:
            open_with(out_file)
