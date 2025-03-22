import os
import subprocess
import sys

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    style_path = os.path.join(script_dir, "style.css")
    # --border-top=1mm --border-bottom=1mm
    subprocess.check_call(
        ["mdpdf", "--style=" + style_path, "--format=Letter", sys.argv[1]],
        shell=True,
    )
