import os
import tempfile

from _shutil import call_echo, wait_until_file_modified
from utils.editor import open_code_editor

call_echo(["adb", "root"])
call_echo(["adb", "remount"])

f = "{{FILE}}"
file_name = os.path.basename(f)
tmp_file = os.path.join(tempfile.gettempdir(), file_name)

call_echo(["adb", "pull", f, tmp_file])

print("Please modify the file...")
open_code_editor(tmp_file)
wait_until_file_modified(tmp_file)

print("Push file to device...")
call_echo(["adb", "push", tmp_file, f])
