from _shutil import *

chdir('..')

script_file = get_files()[0]
link_file = os.path.splitext(os.path.basename(script_file))[0] + '.link'
with open(link_file, 'w', encoding='utf-8') as f:
    f.write(script_file)
print('Link created: %s' % link_file)
