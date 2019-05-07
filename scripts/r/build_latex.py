import os
import glob
import subprocess
import sys

TEX_FILE_FOLDER = r'{{TEX_FILE_FOLDER}}'
assert os.path.exists(TEX_FILE_FOLDER)
os.chdir(TEX_FILE_FOLDER)

list_of_files = glob.glob('*.tex')
latest_file = max(list_of_files, key=os.path.getctime)
name_no_ext = os.path.splitext(latest_file)[0]

# Build pdf
ret = subprocess.call(['pdflatex', name_no_ext + '.tex'])
assert ret == 0

# Convert to png
ret = subprocess.call([
    'magick',
    '-density', '300',
    name_no_ext + '.pdf',
    '-flatten', name_no_ext + '.png'
])
assert ret == 0

# Delete auxiliary files
tmp_files = ['*.aux', '*.fls', '*.log', '*-cache.yaml']
tmp_files = sum([glob.glob(x) for x in tmp_files], [])
for f in tmp_files:
    os.remove(f)
