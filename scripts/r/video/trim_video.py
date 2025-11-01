import argparse
import os
import re
import subprocess
import tempfile

# === CONFIG ===
FREEZE_DB = "-50dB"  # noise threshold — lower for more sensitivity
DEFAULT_MIN_FREEZE_DURATION = 0.5  # seconds - minimum "still" segment to trim
DEFAULT_PRE_PADDING = 0.2  # seconds of padding before kept segments
DEFAULT_POST_PADDING = 0  # seconds of padding after kept segments
# ==========================


def detect_freezes(input_file, min_freeze_duration):
    """Run FFmpeg freezedetect and return list of (start, end) times."""
    pattern_start = re.compile(r"freeze_start:\s*([0-9.]+)")
    pattern_end = re.compile(r"freeze_end:\s*([0-9.]+)")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        input_file,
        "-vf",
        f"freezedetect=n={FREEZE_DB}:d={min_freeze_duration}",
        "-map",
        "0:v:0",
        "-f",
        "null",
        "-",
    ]

    # FFmpeg writes freeze info to stderr
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    lines = proc.stderr.splitlines()

    freezes = []
    current_start = None
    for line in lines:
        if m := pattern_start.search(line):
            current_start = float(m.group(1))
        elif m := pattern_end.search(line):
            if current_start is not None:
                end = float(m.group(1))
                freezes.append((current_start, end))
                current_start = None
    return freezes


def build_segments(freezes, duration, min_freeze_duration, pre_padding, post_padding):
    """Build segments (start, end) to KEEP while limiting freezes to min_freeze_duration."""
    keeps = []
    cursor = 0.0
    for start, end in freezes:
        freeze_len = end - start
        if freeze_len <= min_freeze_duration:
            continue

        pre_end = max(start, cursor)
        if pre_end > cursor:
            keeps.append((cursor, pre_end))

        freeze_keep_start = max(cursor, start)
        freeze_keep_end = min(start + min_freeze_duration, end)
        if freeze_keep_end > freeze_keep_start:
            keeps.append((freeze_keep_start, freeze_keep_end))

        cursor = max(cursor, min(end, duration))

    if cursor < duration:
        keeps.append((cursor, duration))

    padded_keeps = []
    for start, end in keeps:
        padded_start = max(0.0, start - pre_padding)
        padded_end = min(duration, end + post_padding)
        if padded_keeps and padded_start <= padded_keeps[-1][1]:
            last_start, last_end = padded_keeps[-1]
            padded_keeps[-1] = (last_start, max(last_end, padded_end))
        else:
            padded_keeps.append((padded_start, padded_end))

    return padded_keeps


def get_video_duration(filename):
    """Get duration using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        filename,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return float(res.stdout.strip())


def make_concat_file(segments, input_file):
    """Create FFmpeg concat file listing."""
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
    for i, (start, end) in enumerate(segments):
        tmp.write(f"file '{os.path.abspath(input_file)}'\n")
        tmp.write(f"inpoint {start}\n")
        tmp.write(f"outpoint {end}\n")
    tmp.close()
    return tmp.name


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument(
        "-f",
        "--min-freeze-duration",
        type=float,
        default=DEFAULT_MIN_FREEZE_DURATION,
    )
    parser.add_argument(
        "--pre-padding",
        type=float,
        default=DEFAULT_PRE_PADDING,
    )
    parser.add_argument(
        "--post-padding",
        type=float,
        default=DEFAULT_POST_PADDING,
    )
    args = parser.parse_args()

    input_file = args.input_file
    min_freeze_duration = args.min_freeze_duration
    pre_padding = args.pre_padding
    post_padding = args.post_padding
    base_dir = os.path.dirname(input_file)
    stem = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(base_dir, f"{stem}_trimmed.mp4")

    print(f"Analyzing {input_file} for static (> {min_freeze_duration}s) sections ...")
    freezes = detect_freezes(input_file, min_freeze_duration)
    if not freezes:
        print("No static sections detected")
        return

    duration = get_video_duration(input_file)
    print(f"Video duration: {duration:.2f}s")
    print("Detected frozen intervals:")
    for s, e in freezes:
        print(f"  {s:.2f} - {e:.2f} ({e - s:.2f}s)")

    keeps = build_segments(
        freezes, duration, min_freeze_duration, pre_padding, post_padding
    )
    print("Keeping segments:")
    for s, e in keeps:
        print(f"  {s:.2f} - {e:.2f} ({e - s:.2f}s)")
    if pre_padding or post_padding:
        print(f"Applied padding: pre={pre_padding}s, post={post_padding}s")

    concat_file = make_concat_file(keeps, input_file)

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "panic",
        "-safe",
        "0",
        "-f",
        "concat",
        "-segment_time_metadata",
        "1",
        "-i",
        concat_file,
        "-vf",
        "select=concatdec_select",
        "-af",
        "aselect=concatdec_select",
        "-movflags",
        "+faststart",
        output_file,
    ]
    print("Trimming video...")
    subprocess.run(cmd)

    os.remove(concat_file)
    print(f"Done! Output saved to {output_file}")


if __name__ == "__main__":
    _main()
