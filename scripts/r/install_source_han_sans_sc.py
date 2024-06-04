import glob
import os
import subprocess
import sys
import tempfile

from _shutil import copy, download, remove, unzip


def install_font(url):
    if sys.platform != "win32":
        raise OSError("This function can only be run on Windows.")

    tmp_dir = os.path.join(tempfile.gettempdir(), "SourceHanSansSC")
    os.makedirs(tmp_dir, exist_ok=True)
    os.chdir(tmp_dir)

    download(url)
    unzip(os.path.basename(url))

    for f in glob.glob(os.path.join("**", "*.otf"), recursive=True):
        src_file = os.path.basename(f)
        font_name = os.path.splitext(src_file)[0]
        dst_file = os.path.join(r"C:\Windows\Fonts", os.path.basename(f))
        copy(f, dst_file)
        subprocess.check_output(
            [
                "reg",
                "add",
                r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                "/v",
                font_name,
                "/t",
                "REG_SZ",
                "/d",
                dst_file,
                "/f",
            ],
            shell=True,
        )

    remove(tmp_dir)


if __name__ == "__main__":
    install_font(
        "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip"
    )
