import myutils
import os
import re
script = os.getenv('ROSS_SELECTED_SCRIPT_PATH')

with open(script, 'r') as f:
    s = f.read()

match = re.findall('^import _[a-z]$', s, flags=re.MULTILINE)
print(match)