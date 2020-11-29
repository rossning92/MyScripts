import postprocess
import subprocess
from _shutil import *
import importlib


test_file = r"{{_TEST_FILE}}"
ps = None
last_mtime = 0

tmp_dir = os.path.join(tempfile.gettempdir(), "post_process_test")
os.makedirs(tmp_dir, exist_ok=True)
os.chdir(tmp_dir)

while True:
    mtime = os.path.getmtime(postprocess.__file__)
    if mtime > last_mtime:
        if ps != None:
            kill_proc(ps)

        try:
            print("reload module...")
            importlib.reload(postprocess)

            out = postprocess._process_audio_file(test_file, out_dir="tmp")
            ps = subprocess.Popen(["ffplay", "-nodisp", "-loop", "0", out])
        except Exception as ex:
            print(ex)

        last_mtime = mtime

    sleep(1)
