import os

from _shutil import call2, call_echo, cd, get_current_folder, get_files, print2


def convert_to_gif(
    in_file,
    out_file=None,
    optimize=False,
    height=None,
    single_pallete=False,
    fps=15,
    start=None,
    duration=None,
):
    # Convert video to gif
    # fps=25,scale=w=-1:h=480
    if out_file is None:
        out_file = os.path.join("out", os.path.splitext(in_file)[0] + ".gif")

    args = [f"ffmpeg", "-i", in_file]

    # start
    if start is not None and duration is not None:
        args += [
            "-ss",
            f"{start}",
            "-strict",
            "-2",
            "-t",
            f"{duration}",
        ]

    # Filter complex
    filter = f"[0:v] fps={fps}"
    if height is not None:
        filter += f",scale=-1:{height}"
    filter += ",split[a][b];"

    if single_pallete:
        filter += "[a]palettegen[p];[b][p]paletteuse"
    else:
        filter += "[a]palettegen=stats_mode=single[p];[b][p]paletteuse=new=1"

    args += ["-filter_complex", filter]

    args += [out_file, "-y"]

    call_echo(args)

    # Optimize gif
    if optimize:
        print2("Optimize gif...")
        out_gif_optimized = os.path.join(
            "out", os.path.splitext(f)[0] + ".optimized.gif"
        )
        args = f'magick "{out_file}" -coalesce -fuzz 4%% +dither -layers Optimize "{out_gif_optimized}"'
        call2(args)


if __name__ == "__main__":
    fps = int("{{_FPS}}") if "{{_FPS}}" else 15
    height = int("{{_SCALE_H}}") if "{{_SCALE_H}}" else None
    optimize = bool("{{_OPTIMIZE_GIF}}")
    single_pallete = bool("{{_SINGLE_PALETTE}}")

    start, duration = None, None
    if "{{_START_AND_DURATION}}":
        start, duration = [float(x) for x in "{{_START_AND_DURATION}}".split()]

    cur_folder = get_current_folder()
    print("Current folder: %s" % cur_folder)
    os.makedirs(os.path.join(cur_folder, "out"), exist_ok=True)
    cd(cur_folder)

    for f in get_files(cd=True):
        in_file = os.path.basename(f)

        convert_to_gif(
            in_file,
            optimize=optimize,
            height=height,
            fps=fps,
            single_pallete=single_pallete,
            start=start,
            duration=duration,
        )
