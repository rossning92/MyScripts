from _shutil import *


def _images_to_video(out_file, image_files, fps):
    txt_body = '\n'.join(["file '%s'" % x for x in image_files])
    txt_file = write_temp_file(txt_body, '.txt')

    if 1:
        call2([
            'ffmpeg',
            '-r', str(fps),
            '-f', 'concat', '-safe', '0',
            '-i', txt_file,
            '-vcodec', 'prores_ks',
            '-pix_fmt', 'yuva444p10le',
            '-alpha_bits', '16',
            '-profile:v', '4444',
            '-f', 'mov',
            out_file, '-y'
        ])
    else:
        call2([
            'ffmpeg',
            '-r', str(fps),
            '-f', 'concat', '-safe', '0',
            '-i', txt_file,
            '-vcodec', 'libx264',
            '-preset', 'fast',
            '-crf', '22',
            '-f', 'mov',
            out_file, '-y'
        ])


def convert_to_mov(tar_file, fps, out_file=None):
    out_files = []
    name = os.path.splitext(tar_file)[0]
    if out_file is None:
        out_file = name

    tmp_folder = tempfile.gettempdir() + os.path.sep + \
        os.path.basename(name)

    # Unzip
    print2('Unzip to %s' % tmp_folder)
    shutil.unpack_archive(tar_file, tmp_folder)

    # Get all image files
    image_files = sorted(glob.glob((os.path.join(tmp_folder, '*.png'))))

    # Meta file
    meta = None
    if os.path.exists(name + '.json'):
        with open(name + '.json', 'r', encoding='utf-8') as f:
            meta = json.load(f)

    if meta and len(meta['cutPoints']) > 0:
        # convert to index
        indices = [int(round(x * fps)) for x in meta['cutPoints']]
        indices.insert(0, 0)  # prepend frame 0
        indices.append(len(image_files))  # append last frame index + 1

        n = 0
        for i in range(len(indices)-1):
            sub_image_files = image_files[indices[i]:indices[i+1]]

            f = ('%s.mov' % out_file) if (n == 0) else ('%s.%d.mov' % (out_file, n))
            _images_to_video(f, sub_image_files, fps)
            out_files.append(f)

            n += 1

    else:
        f = '%s.mov' % out_file
        _images_to_video(f, image_files, fps)
        out_files.append(f)

    remove(tmp_folder)

    return out_files


if __name__ == '__main__':
    f = sys.argv[-1]
    name, ext = os.path.splitext(f)
    if ext != '.tar':
        print('Input file should be a .tar file')
        sys.exit(1)

    convert_to_mov(f, fps=int('{{_FPS}}'))
