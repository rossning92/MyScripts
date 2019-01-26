from _shutil import *

chdir(r'{{GRAPHVIZ_SRC_FOLDER}}')
src_file = list(glob.glob('*.dot'))[0]
dst_file = os.path.splitext(src_file)[0] + '.png'

call(f'cmd /c dot -Tpng {src_file} -o {dst_file} & {dst_file}')
