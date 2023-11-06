import argparse

from _video import ffmpeg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("start", type=float)
    parser.add_argument("duration", nargs="?", default=None, type=float)
    args = parser.parse_args()

    ffmpeg(
        in_file=args.file,
        start=args.start,
        duration=args.duration,
        reencode=False,
    )
