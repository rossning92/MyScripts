from _shutil import *
import shutil

assert r'{{VIDEO_PROJECT_DIR}}'
dst_dir = os.path.realpath(r'{{VIDEO_PROJECT_DIR}}/footage')

src_files = os.path.realpath(
    os.path.expanduser('~/Documents/ShareX/Screenshots/**/*'))

for src_file in glob.glob(src_files, recursive=True):
    if os.path.isdir(src_file):
        continue

    dst_file = os.path.join(dst_dir, os.path.basename(src_file))

    call2('%s => %s' % (src_file, dst_file))
    shutil.move(src_file, dst_file)

start_process(['explorer', dst_dir])
