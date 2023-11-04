import argparse

from _video import ffmpeg

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument("start")
parser.add_argument("duration")
args = parser.parse_args()


ffmpeg(
    in_file=args.file,
    start_and_duration=(float(args.start), float(args.duration)),
    reencode=False,
)
