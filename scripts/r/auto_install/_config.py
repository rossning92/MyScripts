import os
import sys

BIN_PATH = os.path.abspath(os.path.dirname(__file__) + '/../../../tmp/bin')
print('BIN_PATH: %s' % BIN_PATH)

CHOCO_PKG_MAP = {
    'notepad++': 'notepadplusplus',
    'conemu': 'conemu',
    '7z': '7zip',
    'sumatrapdf': 'sumatrapdf',
    'git': 'git'
}
