import os

from _shutil import get_files, mkdir
from _video import ffmpeg, hstack_videos
from open_with.open_with import open_with


if __name__ == "__main__":
    files = get_files(cd=True)

    crop_rect = (
        [int(x) for x in "{{_CROP_RECT}}".split()[0:4]] if "{{_CROP_RECT}}" else None
    )

    start_and_duration = (
        "{{_START_AND_DURATION}}".split() if "{{_START_AND_DURATION}}" else None
    )

    for f in files:
        if not os.path.isfile(f):
            continue

        mkdir("out")
        name = os.path.basename(os.path.splitext(f)[0])
        out_file = "out/%s.mp4" % name

        extra_args = []

        if "{{_SPEED}}":
            filter_a = "atempo={{_SPEED}}"
            extra_args += ["-filter:a", filter_a]

        if "{{_FIND_BEST_CRF}}":
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
                crf=int("{{_CRF}}") if "{{_CRF}}" else 19,
                start_and_duration=start_and_duration,
                nvenc=bool("{{_NVENC}}"),
                max_size_mb=float("{{_MAX_SIZE_MB}}") if "{{_MAX_SIZE_MB}}" else None,
                no_audio=bool("{{_NO_AUDIO}}"),
                loop=float("{{_LOOP}}") if "{{_LOOP}}" else None,
                crop_rect=crop_rect,
                to_anamorphic=True if "{{_TO_ANAMORPHIC}}" else False,
                crop_to_1080p=True if "{{_CROP_TO_1080P}}" else False,
                pad_to_1080p=True if "{{_PAD_TO_1080P}}" else False,
                rotate_cw=True if "{{_ROTATE_CW}}" else False,
                rotate_ccw=True if "{{_ROTATE_CCW}}" else False,
                speed=float("{{_SPEED}}") if "{{_SPEED}}" else None,
                height=int("{{_HEIGHT}}") if "{{_HEIGHT}}" else None,
                width=int("{{_WIDTH}}") if "{{_WIDTH}}" else None,
                title="{{_TITLE}}",
                reverse=True if "{{_REVERSE}}" else False,
                remove_duplicated_frames=True
                if "{{_REMOVE_DUPLICATED_FRAMES}}"
                else False,
                test=True if "{{_TEST}}" else False,
                fps=int("{{_FPS}}") if "{{_FPS}}" else None,
            )

        if len(files) == 1:
            open_with(out_file)
