from _shutil import *

script_root = os.path.realpath(os.path.realpath(__file__) + '/../../')

script_path = os.environ['_SCRIPT']

# Get relative path
script_path = re.sub('^' + re.escape(script_root), '', script_path)
script_path = script_path.replace('\\', '/')

print('Script path copied: %s' % script_path)
set_clip(script_path)
