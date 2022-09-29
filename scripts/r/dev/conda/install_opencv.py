from _shutil import *
import _conda

_conda.setup_env()
call('conda install -c conda-forge opencv -y')