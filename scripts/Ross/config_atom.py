import cson
import os

cfg_file = os.path.expanduser('~/.atom/config.cson')

with open(cfg_file, 'r') as f:
    obj = cson.loads(f.read())

obj['*']['latex'] = {'useDicy': True}
obj['*']['markdown-image-assistant'] = {'preserveFileNameInAssetsFolder': True}

with open(cfg_file, 'w') as f:
    f.write(cson.dumps(obj, indent=2))
