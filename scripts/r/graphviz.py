from _shutil import *

chdir(r'{{GRAPHVIZ_SRC_FOLDER}}')
files = list(glob.glob('*.dot'))
files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
src_file = files[0]

fmt = 'png'
dst_file = os.path.splitext(src_file)[0] + f'.{fmt}'

call(f'cmd /c dot -T{fmt} "{src_file}" -o "{dst_file}"')
Popen([r"C:\Program Files\IrfanView\i_view64.exe", dst_file])
