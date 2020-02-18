from _shutil import *

f = sys.argv[-1]
name, ext = os.path.splitext(f)
if ext != '.tar':
    print('Input file should be a .tar file')
    sys.exit(1)


tmp_folder = tempfile.gettempdir() + os.path.sep + \
    os.path.basename(os.path.splitext(f)[0])

# Unzip
print2('Unzip to %s' % tmp_folder) 
shutil.unpack_archive(f, tmp_folder)

# Convert
in_file = os.path.join(tmp_folder, '%07d.png')
out_file = name + '.mov'
call2([
    'ffmpeg',
    '-r', '{{_FPS}}',
    '-i', in_file,
    '-vcodec', 'prores_ks',
    '-pix_fmt', 'yuva444p10le',
    '-alpha_bits', '16',
    '-profile:v', '4444',
    '-f', 'mov',
    out_file, '-y'
])
remove(tmp_folder)
