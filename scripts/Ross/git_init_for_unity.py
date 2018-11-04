import os
import sys
from urllib.request import urlretrieve


os.chdir(os.environ['CURRENT_FOLDER'])

urlretrieve('https://raw.githubusercontent.com/github/gitignore/master/Unity.gitignore', '.gitignore')


