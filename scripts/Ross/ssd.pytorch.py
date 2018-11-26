from _shutil import *

mkdir(r'{{PROJECT_DIR}}')
chdir(r'{{PROJECT_DIR}}')

if not exists('ssd.pytorch'):
    call('git clone https://github.com/amdegroot/ssd.pytorch')

chdir('ssd.pytorch')

# Conda path
dirs = [
    r'C:\tools\miniconda3',
    r'C:\tools\miniconda3\Scripts'
]
os.environ["PATH"] = os.pathsep.join(dirs) + os.pathsep + os.environ["PATH"]

call('pip install visdom', shell=True)

mkdir('weights')
chdir('weights')
download('https://s3.amazonaws.com/amdegroot-models/ssd300_mAP_77.43_v2.pth')
chdir('..')

call('conda install opencv -y', shell=True)

#call('pip install imutils', shell=True)
#call('python -m demo.live', shell=True)


call('pip3 install --upgrade pip')
call('pip install jupyter')
call('jupyter notebook')