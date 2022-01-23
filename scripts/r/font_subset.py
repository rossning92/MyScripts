import os
import subprocess
import sys

from _shutil import call_echo, get_files

if __name__ == "__main__":
    # Simplify / create font subset by specify characters to include.
    # https://github.com/kaienfr/Font/blob/master/learnfiles/%E5%B8%B8%E7%94%A8%E6%B1%89%E5%AD%97%E5%BA%93%203500.txt
    common_zh_chars_file = os.path.join(
        os.path.realpath(os.path.dirname(__file__)), "common_zh_chars.txt"
    )
    with open(common_zh_chars_file, encoding="utf-8") as f:
        text = f.read()

    in_font = get_files()[0]
    call_echo([sys.executable, "-m", "pip", "install", "fonttools"])
    subprocess.check_call(["pyftsubset", in_font, f"--text={text}"])
