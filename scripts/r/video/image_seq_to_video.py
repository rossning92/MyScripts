from _video import *
from _shutil import *


fps = "{{_FPS}}" if "{{_FPS}}" else "60"

cd(os.environ["_CUR_DIR"])

exec_bash(
    f"ffmpeg -r {fps} -i %04d.png  -vcodec mjpeg  -vcodec libx264 -crf 19 out.mp4 -y"
)
