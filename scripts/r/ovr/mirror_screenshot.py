import subprocess
import datetime
import os

os.chdir(os.path.join(os.environ['USERPROFILE'], 'Desktop'))

exe = r'C:\Program Files\Oculus\Support\oculus-diagnostics\OculusMirror.exe'
file_name = '%s.png' % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
args = [
    exe,
    '--PostDistortion',
    '--Screenshot', file_name
]
subprocess.call(args)