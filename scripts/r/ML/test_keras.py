from _shutil import *
from _git import *

git_clone('https://github.com/keras-team/keras')

cd('examples')

call_echo('pip install keras')
call_echo('python cifar10_resnet.py --help')
