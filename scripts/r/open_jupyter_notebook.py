from _conda import setup_env
from _shutil import *
import os

setup_env()

call(f'call activate & jupyter notebook "{os.environ["SELECTED_FILE"]}"')
