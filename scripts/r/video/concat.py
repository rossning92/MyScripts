import os
import subprocess

from _shutil import get_files, write_temp_file

if __name__ == "__main__":
    files = get_files()

    file_list = write_temp_file("\n".join(["file '%s'" % f for f in files]), ".txt")
    os.chdir(os.environ["CWD"])
    subprocess.check_call(
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
            "concat.mp4",
            "-y",
        ]
    )
