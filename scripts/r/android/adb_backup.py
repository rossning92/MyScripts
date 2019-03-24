from _shutil import *

APP = 'com.coolapk.market'
APP = 'cn.mdict'

d = 'C:\\tools\\abe'
mkdir(d)
chdir(d)

download('https://github.com/nelenkov/android-backup-extractor/releases/download/20181012025725-d750899/abe-all.jar')

chdir(expanduser('~/Desktop'))

call(f'adb backup -apk -f backup.ab {APP}')

call(f'java -jar "{d}/abe-all.jar" unpack backup.ab backup.tar')
