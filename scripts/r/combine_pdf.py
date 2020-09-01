from _shutil import *

pdftk = r'C:\Program Files (x86)\PDFtk\bin\pdftk.exe'
if not exists(pdftk):
    run_elevated('choco install pdftk -y')

chdir(env['_CUR_DIR'])

files = env['_FILES'].split('|')
print('Files to combine:', files)

call([pdftk] + files + ['cat', 'output', 'Combined.pdf'])
