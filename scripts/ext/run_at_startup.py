from _shutil import *

path = os.path.realpath('../../run.cmd')

call2('reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v MyScripts /t REG_SZ /d """' +
      path + '""" /f')
