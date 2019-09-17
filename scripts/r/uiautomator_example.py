from _shutil import *
from _android import *

setup_android_env()

# https://github.com/xiaocong/uiautomator

call('pip install uiautomator')

call('python -c "import code; from uiautomator import device as d; code.interact(local=locals())"')
