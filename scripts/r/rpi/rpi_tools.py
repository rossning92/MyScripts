import ctypes
import os
import tempfile

from _shutil import (
    call_echo,
    download,
    find_newest_file,
    menu_item,
    menu_loop,
    print2,
    unzip,
    confirm,
)

# https://www.raspberrypi.com/software/operating-systems/
url = "https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2021-05-28/2021-05-07-raspios-buster-armhf-lite.zip"


def get_all_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in map(chr, range(65, 91)):
        if bitmask & 1:
            drives.append(letter + ":")
        bitmask >>= 1
    return drives


@menu_item(key="s")
def setup_wifi_and_ssh():
    print("Configuring wifi...")
    drive_found = False
    for drive in get_all_drives():
        if os.path.exists(os.path.join(drive, "bootcode.bin")):
            # https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-headless-raspberry-pi
            if confirm("Found raspi boot partition at: %s" % drive):
                wifi_ssid = r"{{WIFI_SSID}}"
                wifi_pwd = r"{{WIFI_PWD}}"
                with open(
                    os.path.join(drive, "wpa_supplicant.conf"), "w", newline="\n"
                ) as f:
                    print("Write wpa_supplicant.conf file...")
                    content = (
                        "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n"
                        "country=US\n"
                        "update_config=1\n"
                        "\n"
                        "network={\n"
                        f'  ssid="{wifi_ssid}"\n'
                        f'  psk="{wifi_pwd}"\n'
                        "}\n"
                    )
                    print2(content, color="black")
                    f.write(content)

                # Enable ssh
                print("Touch ssh file...")
                with open(os.path.join(drive, "ssh"), "a") as f:
                    pass

                drive_found = True
                break

    if not drive_found:
        print2("ERROR: No drive found.", color="red")
    print("Done.")


@menu_item(key="f")
def flash_raspi_os():
    os.chdir(tempfile.gettempdir())

    out = download(url)
    if not os.path.exists("raspios"):
        unzip(out, "raspios")

    img_file = find_newest_file("raspios/**/*.img")
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
        return

    call_echo(
        [r"C:\Program Files (x86)\Raspberry Pi Imager\rpi-imager-cli.cmd", img_file, s]
    )


if __name__ == "__main__":
    menu_loop()
