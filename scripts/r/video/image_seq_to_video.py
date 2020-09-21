from _video import *
from _shutil import *


fps = "{{_FPS}}" if "{{_FPS}}" else "60"

cd(os.environ["_CUR_DIR"])

exec_bash(
    f"cat *.png | ffmpeg -f image2pipe -r {fps} -vcodec png -i - -vcodec libx264 out.mp4 -y"
)
