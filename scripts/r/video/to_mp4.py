import os

from _shutil import get_files, mkdir, setup_logger
from _video import ffmpeg, hstack_videos
from open_with.open_with import open_with

if __name__ == "__main__":
    setup_logger()
    files = get_files(cd=True)

    crop_rect = (
        [int(x) for x in os.environ["_CROP_RECT"].split()[0:4]]
        if os.environ.get("_CROP_RECT")
        else None
    )

    start_and_duration = (
        os.environ["_START_AND_DURATION"].split()
        if os.environ.get("_START_AND_DURATION")
        else None
    )

    for f in files:
        if not os.path.isfile(f):
            continue

        mkdir("out")
        name = os.path.basename(os.path.splitext(f)[0])
        out_file = "out/%s.mp4" % name

        extra_args = []

        if os.environ.get("_FIND_BEST_CRF"):
            out_files = []
            for crf in [22, 26, 30, 34, 38]:
                extra_args += ["-crf", str(crf)]
                out_files.append(
                    ffmpeg(
                        f,
                        out_file="out/{}_crf{}.mp4".format(name, crf),
                        start_and_duration=(
                            (0, 5) if start_and_duration is None else start_and_duration
                        ),
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
                f,
                out_file=out_file,
                extra_args=extra_args,
                nvenc=bool(env.get("_NVENC")),
                crf=int(env.get("_CRF", 19)),
                max_size_mb=(
                    float(env["_MAX_SIZE_MB"]) if env.get("_MAX_SIZE_MB") else None
                ),
                start_and_duration=start_and_duration,
                fps=int(env["_FPS"]) if env.get("_FPS") else None,
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

        if env.get("_OPEN") and len(files) == 1:
            open_with(out_file)
