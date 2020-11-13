from _shutil import *

pdftk = r'C:\Program Files (x86)\PDFtk\bin\pdftk.exe'
if not exists(pdftk):
    run_elevated('choco install pdftk -y')

chdir(env['CUR_DIR_'])

files = env['FILES_'].split('|')
print('Files to combine:', files)

call([pdftk] + files + ['cat', 'output', 'Combined.pdf'])
