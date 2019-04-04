from _shutil import *

NVPACK = r"{{UE_SOURCE}}\Engine\Extras\AndroidWorks\Win64\CodeWorksforAndroid-1R6u1-windows.exe"

print('Install NVPACK...')
run_elevated([NVPACK])

print('BUG: NVPACK installs Build-Tools 26.0.1 by default')
print('     26.0.2 is needed.')
input('Press any key...')
chdir(r'C:\NVPACK\android-sdk-windows\tools\bin')
call('sdkmanager build-tools;26.0.2')