from _shutil import *


def setup_py27():
    assert exists(r'C:\Python27')
    prepend_to_path([
        r'C:\Python27',
        r'C:\Python27\Scripts'
    ])
