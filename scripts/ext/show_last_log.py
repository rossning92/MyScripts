import glob
import os
import myutils

wildcard = os.path.join(os.environ['USERPROFILE'], 'ConEmu', 'Logs', '*.log')
files = glob.glob(wildcard)
files.sort(key=os.path.getmtime)
myutils.open_text_editor(files[-1])
