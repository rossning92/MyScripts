import importlib
import os
import subprocess
import tempfile
import time

from _shutil import kill_proc

import postprocess

test_file = r"{{_TEST_FILE}}"
ps = None
last_mtime = 0.0

os.chdir(os.path.dirname(test_file))

while True:
    mtime = os.path.getmtime(postprocess.__file__)
    if mtime > last_mtime:
        if ps != None:
            kill_proc(ps)

        try:
            print("reload module...")
            importlib.reload(postprocess)

            out = postprocess.process_audio_file(test_file, "tmp/test.wav")
            ps = subprocess.Popen(["ffplay", "-nodisp", "-loop", "0", out])
        except Exception as ex:
            print(ex)

        last_mtime = mtime

    time.sleep(1)
