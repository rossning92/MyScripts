import _conda; _conda.setup_env()
from _shutil import *
import os

call(f'call activate & jupyter notebook "{os.environ["SELECTED_FILE"]}"')
