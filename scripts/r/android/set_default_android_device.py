import subprocess
from _script import set_variable
from _shutil import print2, getch


lines = subprocess.check_output(["adb", "devices"], universal_newlines=True).split("\n")
lines = lines[1:]
serial_list = []
for line in lines:
    if line.strip():
        serial, _ = line.split()
        serial_list.append(serial)
        print("[%d] %s" % (len(serial_list), serial))


ch = getch()
index = ord(ch) - ord("1")
if index >= 0 and index < len(serial_list):
    set_variable("ANDROID_SERIAL", serial_list[index])
    print2("Set default device to %s" % serial_list[index])
