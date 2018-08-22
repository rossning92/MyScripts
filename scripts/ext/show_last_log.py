import glob
import os
import myutils

wildcard = os.path.join(os.environ['TEMP'], 'Log_*.txt')
files = glob.glob(wildcard)
myutils.open_text_editor(files[-1])
