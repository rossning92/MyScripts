import os
import subprocess
import sys
from _shutil import *


os.system('taskkill /f /im OculusMirror.exe')
os.chdir(r"C:\Program Files\Oculus\Support\oculus-diagnostics")

run_elevated('REG ADD "HKLM\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /V "C:\Program Files\Oculus\Support\oculus-diagnostics\OculusMirror.exe" /T REG_SZ /D "~ HIGHDPIAWARE" /F')

# OculusMirror
#   [--help /?]
#   [--LeftEyeOnly] [--RightEyeOnly [--RectilinearBothEyes]
#   [--PostDistortion] [--DisableTimewarp] [--FovTanAngleMultiplier x y]
#   [--IncludeGuardian] [--IncludeNotifications]
#   [--Size width height]
#   [--Screenshot dirPath]
# 1366 768    2160 1080    1080 600     1296 720

args = [
    'OculusMirror.exe',
    # '--Size', '1296', '720'
]
if "{{POST_DISTORTION}}" == "Y":
    args.append('--PostDistortion')
else:
    args.append('--RectilinearBothEyes')
if '{{MIRROW_LEFT_EYE}}':
    args.append('--LeftEyeOnly')
    args += ['--Size', '1080', '1200']

if '{{MIRROR_SAVE_IMG}}':
    args += ['--Screenshot', expanduser('~/Desktop/Mirror_%s.png' % get_cur_time_str())]

subprocess.Popen(args)
