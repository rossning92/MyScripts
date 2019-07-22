import os
import subprocess
from _cmake import setup_cmake

try:
    import _setup_android_env as android
    android.setup_android_env()
except:
    print('[WARNING] Android env not found.')

if 'CURRENT_FOLDER' in os.environ:
    os.chdir(os.environ['CURRENT_FOLDER'])
else:
    os.chdir(os.path.expanduser('~'))

setup_cmake()

subprocess.call(['cmd'])
