import os
import datetime
import subprocess
import sys

dt = datetime.datetime.now()
file_name = dt.strftime('Temp_%Y%m%d_%H%M%S.cmd')

#with open(file_name, 'w') as f:
#    pass

if sys.platform == 'darwin':
    subprocess.Popen(['atom'])
else:
    subprocess.Popen(['notepad++'])
