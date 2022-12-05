import os
import sys

from _shutil import call_echo, download, find_newest_file, get_home_path, print2

# https://www.raspberrypi.com/software/operating-systems/
RASPI_OS_DOWNLOAD_URL = "https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2022-09-26/2022-09-22-raspios-bullseye-armhf-lite.img.xz"


if __name__ == "__main__":
    download_dir = os.path.join(get_home_path(), "Downloads")
    os.chdir(download_dir)

    out = download(RASPI_OS_DOWNLOAD_URL)

    # unzip
    out_dir = os.path.splitext(out)[0]
    if not os.path.exists(out_dir):
        call_echo(["run_script", "r/unzip.py", out])

    img_file = find_newest_file(os.path.join(out_dir, "*.img"))
    if img_file is None:
        raise Exception("Cannot find image file to write.")

    call_echo(
        [
            r"C:\Program Files (x86)\Raspberry Pi Imager\rpi-imager-cli.cmd",
            img_file,
            "(invalid)",
        ]
    )

    print2("Please paste the volume here: ", end="")
    s = input()
    if not s:
        sys.exit(0)

    call_echo(
        [r"C:\Program Files (x86)\Raspberry Pi Imager\rpi-imager-cli.cmd", img_file, s]
    )
