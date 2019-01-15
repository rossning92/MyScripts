import _conda
from _shutil import *
import os

call('jupyter notebook "%s"' % os.environ['SELECTED_FILE'])
