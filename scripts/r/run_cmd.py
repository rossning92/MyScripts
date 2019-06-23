import os
import subprocess

try:
    import _setup_android_env as android
    android.setup_android_env()
except:
    print('[WARNING] Android env not found.')

if 'CURRENT_FOLDER' in os.environ:
    os.chdir(os.environ['CURRENT_FOLDER'])
else:
    os.chdir(os.path.expanduser('~'))
subprocess.call(['cmd'])
