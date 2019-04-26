from _shutil import *
from _term import *
import json

data = {}
for k, v in env.items():
    if 'NVPACK' in k or 'NVPACK' in v:
        if k == 'PATH':
            arr = v.split(';')
            arr = [x for x in arr if 'NVPACK' in x]
            data['PATH'] = arr
        else:
            data[k] = v

json_str = json.dumps(data, indent=4)
print(json_str)

if wait_key('backup NVPACK env vars'):
    with open(expanduser('~/NVPACK_env.txt'), 'w') as f:
        f.write(json_str)

for k, v in data.items():
    if k == 'PATH':
        s = check_output('reg query HKCU\Environment /v PATH').decode()
        s = re.search(r'PATH\s+REG_SZ\s+(.*)', s).group(1).strip()
        paths = s.split(';')
        paths = [x for x in paths if x.strip() != '' and x not in data['PATH']]
        s = ';'.join(paths)
        print(f'PATH={s}')
        call(f'reg add HKCU\Environment /v PATH /d "{s}" /f')
    else:
        print(f'Delete ENV: {k}')
        call(f'reg delete "HKCU\Environment" /v {k} /f', check_call=False)
