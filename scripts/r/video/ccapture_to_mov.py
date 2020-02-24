from _shutil import *


def convert_to_mov(tar_file, fps, out_file=None):
    name = os.path.splitext(tar_file)[0]
    tmp_folder = tempfile.gettempdir() + os.path.sep + \
        os.path.basename(name)

    # Unzip
    print2('Unzip to %s' % tmp_folder)
    shutil.unpack_archive(tar_file, tmp_folder)

    # Convert
    in_file = os.path.join(tmp_folder, '%07d.png')
    if out_file is None:
        out_file = name + '.mov'
    call2([
        'ffmpeg',
        '-r', str(fps),
        '-i', in_file,
        '-vcodec', 'prores_ks',
        '-pix_fmt', 'yuva444p10le',
        '-alpha_bits', '16',
        '-profile:v', '4444',
        '-f', 'mov',
        out_file, '-y'
    ])
    remove(tmp_folder)

    return out_file


if __name__ == '__main__':
    f = sys.argv[-1]
    name, ext = os.path.splitext(f)
    if ext != '.tar':
        print('Input file should be a .tar file')
        sys.exit(1)

    convert_to_mov(f, fps=int('{{_FPS}}'))
