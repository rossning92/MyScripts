from _video import *
from _shutil import *


fps = "{{_FPS}}" if "{{_FPS}}" else "60"

cd(os.environ["CUR_DIR_"])

input_file = "input.txt"
files = sorted(glob.glob("*.png"))
with open(input_file, "w") as f:
    for file in files:
        f.write("file '%s'\n" % file)

exec_bash(
    f"ffmpeg -r {fps} -f concat -safe 0 -i {input_file} -vcodec libx264 -crf 19 out.mp4 -y"
)
