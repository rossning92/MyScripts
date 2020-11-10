from _audio import *
from _shutil import *


if __name__ == "__main__":
    files = get_files()

    file_list = write_temp_file("\n".join(["file '%s'" % f for f in files]), ".txt")
    cd(os.environ["CUR_DIR_"])
    call_echo(
        [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            file_list,
            "-c",
            "copy",
            "out/concat.mp4",
            "-y",
        ],
        shell=False,
    )
