from _shutil import *

chdir('..')
cwd = getcwd()
script_path = expandvars("%USERPROFILE%\Google Drive\Scripts")

if (not exists('gdrive')) and (exists(script_path)):
    run_elevated(rf'cmd /c cd /d "{cwd}" & mklink /d gdrive "{script_path}"')
    print2('Create symlink: %s => %s' % ('gdrive', script_path))
