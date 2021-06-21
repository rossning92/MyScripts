from _shutil import *
from _video import *
from open_with.open_with import open_with

crop_rect = (
    [int(x) for x in "{{_CROP_RECT}}".split()[0:4]] if "{{_CROP_RECT}}" else None
)
files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    mkdir("out")
    out_file = "out/%s.mp4" % os.path.basename(os.path.splitext(f)[0])

    extra_args = []

    # FPS
    if "{{_FPS}}":
        extra_args += ["-r", "{{_FPS}}"]

    filter_v = []

    # Crop video
    if crop_rect:
        filter_v.append(
            f"crop={crop_rect[2]}:{crop_rect[3]}:{crop_rect[0]}:{crop_rect[1]}"
        )

    if "{{_TO_ANAMORPHIC}}":
        filter_v.append("scale=1920:-2,crop=1920:816:0:132,pad=1920:1080:0:132")

    elif "{{_CROP_TO_1080P}}":
        filter_v.append("scale=1920:-2,pad=1920:1080:0:0")

    elif "{{_PAD_TO_1080P}}":
        filter_v.append("pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black")

    if "{{_ROTATE_CW}}":
        filter_v.append("transpose=1")
    elif "{{_ROTATE_CCW}}":
        filter_v.append("transpose=2")

    if "{{_SPEED}}":
        filter_v.append("setpts=PTS/%.2f" % float("{{_SPEED}}"))

    # Scale (-2 indicates divisible by 2)
    if "{{_RESIZE_H}}":
        filter_v.append("scale=-2:{{_RESIZE_H}}")
    elif "{{_RESIZE_W}}":
        filter_v.append("scale={{_RESIZE_W}}:-2")

    if "{{_TEXT_OVERLAY}}":
        filter_v.append(
            "drawtext=text='{{_TEXT_OVERLAY}}':fontcolor=white@1.0:fontsize=100:x=(w-text_w)/2:y=(h-text_h)/2"
        )

    if "{{_REVERSE}}":
        filter_v.append("reverse")

    if "{{_REMOVE_DUPLICATED_FRAMES}}":
        filter_v.append("mpdecimate,setpts=N/FRAME_RATE/TB")

    if "{{_TEST}}":
        filter_v.append("setpts=2.0*PTS*(1+random(0)*0.02)")

    if filter_v:
        extra_args += ["-filter:v", ",".join(filter_v)]

    if "{{_SPEED}}":
        filter_a = "atempo={{_SPEED}}"
        extra_args += ["-filter:a", filter_a]

    # Cut video
    start_and_duration = None
    if "{{_START_AND_DURATION}}":
        start_and_duration = "{{_START_AND_DURATION}}".split()

    # Pixel format
    extra_args += ["-pix_fmt", "yuv420p"]

    ffmpeg(
        f,
        out_file=out_file,
        extra_args=extra_args,
        reencode=True,
        crf=int("{{_CRF}}") if "{{_CRF}}" else None,
        start_and_duration=start_and_duration,
        nvenc=bool("{{_NVENC}}"),
        max_size_mb=float("{{_MAX_SIZE_MB}}") if "{{_MAX_SIZE_MB}}" else None,
        no_audio=bool("{{_NO_AUDIO}}"),
    )

    if len(files) == 1:
        open_with(out_file)
