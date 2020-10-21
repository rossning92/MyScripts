from _shutil import *
from _editor import *


call_echo(["adb", "root"])
call_echo(["adb", "remount"])

f = "{{_FILE}}"
file_name = os.path.basename(f)
tmp_file = os.path.join(tempfile.gettempdir(), file_name)

call_echo(["adb", "pull", f, tmp_file])

print("Please modify the file...")
open_in_vscode(tmp_file)
wait_until_file_modified(tmp_file)

print("Push file to device...")
call_echo(["adb", "push", tmp_file, f])
