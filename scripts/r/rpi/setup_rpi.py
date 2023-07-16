import ctypes
import os
import sys

from _shutil import confirm, print2

wifi_ssid = os.environ["WIFI_SSID"]
wifi_pwd = os.environ["WIFI_PWD"]


def get_all_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in map(chr, range(65, 91)):
        if bitmask & 1:
            drives.append(letter + ":")
        bitmask >>= 1
    return drives


if __name__ == "__main__":
    print("Configuring wifi...")
    drive_found = False
    for drive in get_all_drives():
        if os.path.exists(os.path.join(drive, "bootcode.bin")):
            # https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-headless-raspberry-pi
            if confirm("Found raspi boot partition at: %s" % drive):
                # Auto connect to hotspot
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

                # Enable default user
                with open(os.path.join(drive, "userconf"), "w") as f:
                    f.write(
                        "pi:$6$I1eC.nSwKmfke5kE$0rGcIGs7JifCgWGS2u.B2Mfok8CXYYAvgIsulIAakWo/68bGXrj.fvV8Kd16/rQGcMTIyFVTC9tRy3GtToaJ20"
                    )

                drive_found = True
                break

    if not drive_found:
        print2("ERROR: No drive found.", color="red")
        sys.exit(1)
