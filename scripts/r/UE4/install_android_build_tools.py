from _shutil import *
from _script import *

NVPACK = r"{{UE_SOURCE}}\Engine\Extras\AndroidWorks\Win64\CodeWorksforAndroid-*-windows.exe"
NVPACK = glob.glob(NVPACK)[0]

print('Install NVPACK...')
run_elevated([NVPACK])

run_script('/r/UE4/remove_nvpack_env_var.py')

# UE4.20
print('BUG: NVPACK installs Build-Tools 26.0.1 by default. But 26.0.2 is needed.')
if 'y' == input('Do you want to install (y/n)...'):
    chdir(r'C:\NVPACK\android-sdk-windows\tools\bin')
    call('sdkmanager build-tools;26.0.2')

input('You need to run Setup.bat again. Press any key...')
