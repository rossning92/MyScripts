import os

from _shutil import get_files, mkdir
from _video import ffmpeg, hstack_videos
from open_with.open_with import open_with

if __name__ == "__main__":
    files = get_files(cd=True)

    crop_rect = (
        [int(x) for x in os.environ["_CROP_RECT"].split()[0:4]]
        if "_CROP_RECT" in os.environ
        else None
    )

    start_and_duration = (
        os.environ["_START_AND_DURATION"].split()
        if "_START_AND_DURATION" in os.environ
        else None
    )

    for f in files:
        if not os.path.isfile(f):
            continue

        mkdir("out")
        name = os.path.basename(os.path.splitext(f)[0])
        out_file = "out/%s.mp4" % name

        extra_args = []

        if "_SPEED" in os.environ:
            filter_a = "atempo=" + os.environ["_SPEED"]
            extra_args += ["-filter:a", filter_a]

        if "_FIND_BEST_CRF" in os.environ:
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
            ffmpeg(
                f,
                out_file=out_file,
                extra_args=extra_args,
                reencode=True,
                nvenc=bool(os.environ.get("_NVENC")),
                crf=int(os.environ.get("_CRF", 19)),
                max_size_mb=(
                    float(os.environ["_MAX_SIZE_MB"])
                    if "_MAX_SIZE_MB" in os.environ
                    else None
                ),
                start_and_duration=start_and_duration,
                fps=int(os.environ["_FPS"]) if "_FPS" in os.environ else None,
                width=int(os.environ["_WIDTH"]) if "_WIDTH" in os.environ else None,
                height=int(os.environ["_HEIGHT"]) if "_HEIGHT" in os.environ else None,
                no_audio=bool(os.environ.get("_NO_AUDIO")),
                loop=int(os.environ.get("_LOOP", 0)),
                crop_rect=crop_rect,
                add_border=int(os.environ.get("_ADD_BORDER", 0)),
                crop_to_1080p=bool(os.environ.get("_CROP_TO_1080P")),
                pad_to_1080p=bool(os.environ.get("_PAD_TO_1080P")),
                rotate_ccw=bool(os.environ.get("_ROTATE_CCW")),
                rotate_cw=bool(os.environ.get("_ROTATE_CW")),
                speed=float(os.environ.get("_SPEED", 1.0)),
                title=os.environ.get("_TITLE"),
                to_anamorphic=bool(os.environ.get("_TO_ANAMORPHIC")),
                remove_duplicated_frames=bool(
                    os.environ.get("_REMOVE_DUPLICATED_FRAMES")
                ),
                reverse=bool(os.environ.get("_REVERSE")),
            )

        if not os.environ.get("_NO_OPEN") and len(files) == 1:
            open_with(out_file)
