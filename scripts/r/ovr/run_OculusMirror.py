import os
import subprocess
import sys

os.system('taskkill /f /im OculusMirror.exe')
os.chdir(r"C:\Program Files\Oculus\Support\oculus-diagnostics")

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
    '--Size', '1296', '720'
]
if "{{POST_DISTORTION}}" == "Y":
    args.append('--PostDistortion')
else:
    args.append('--RectilinearBothEyes')
subprocess.Popen(args)
