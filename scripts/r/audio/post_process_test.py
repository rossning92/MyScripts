import postprocess
import subprocess
from _shutil import *
import importlib


f = r"C:\Users\Ross\Google Drive\KidslogicVideo\ep27\record\record_081.wav"
ps = None
last_mtime = 0

tmp_dir = os.path.join(tempfile.gettempdir(), "post_process_test")
os.makedirs(tmp_dir, exist_ok=True)
os.chdir(tmp_dir)

while True:
    mtime = os.path.getmtime(postprocess.__file__)
    if mtime > last_mtime:
        if ps != None:
            subprocess_kill(ps)

        try:
            print("reload module...")
            importlib.reload(postprocess)

            out = postprocess.process_audio_file(f, regenerate=True)
            ps = subprocess.Popen(["ffplay", "-nodisp", "-loop", "0", out])
        except Exception as ex:
            print(ex)

        last_mtime = mtime

    sleep(1)
