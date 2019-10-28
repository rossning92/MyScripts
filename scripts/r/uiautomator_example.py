from _shutil import *
from _android import *

setup_android_env()

# https://github.com/xiaocong/uiautomator
# "C:\Android\android-sdk\tools\bin\uiautomatorviewer.bat"

call('pip install uiautomator --upgrade')

call('python -c "import code; from uiautomator import device as d; code.interact(local=locals())"')
