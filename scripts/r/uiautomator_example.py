from _shutil import *

call('pip install uiautomator')
os.environ['ANDROID_HOME'] = expandvars(r'%USERPROFILE%\AppData\Local\Android\Sdk')

call('python -c "import code; from uiautomator import device as d; code.interact(local=locals())"')