from _shutil import cd, get_files, mkdir, call_echo
import os

cd("c:/Users/Ross/Google Drive/KidslogicVideo/ep35/animation/icons")


for f in get_files(cd=True):
    mkdir("shadow")
    out_file = os.path.join("shadow", os.path.basename(f))

    call_echo(
        [
            "magick",
            f,
            "(",
            "-clone",
            "0",
            "-background",
            "black",
            "-shadow",
            "80x5+0+0",
            ")",
            "-reverse",
            "-background",
            "none",
            "-layers",
            "merge",
            "+repage",
            out_file,
        ]
    )
