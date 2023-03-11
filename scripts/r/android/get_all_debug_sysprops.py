import re
import subprocess

from _shutil import print2, read_proc_lines

if __name__ == "__main__":
    try:
        subprocess.check_call(["adb", "root"])
        lines = list(
            read_proc_lines(["adb", "shell", "getprop -Z | grep :debug_oculus_prop:"])
        )

        for line in lines:
            line = line.strip()
            matches = re.findall(r"^\[(.*?)\]", line)
            prop_name = matches[0]
            prop_val = subprocess.check_output(
                ["adb", "shell", "getprop", prop_name], universal_newlines=True
            ).strip()
            if prop_val:
                print("%s\t%s" % (prop_name, prop_val))
    except Exception as e:
        print(e)
        print2("ERROR")
