from _shutil import *

run_elevated('choco install virtualbox --version=6.0.4 -y')
run_elevated('choco install vagrant -y')

cd('~/ubuntu_vm_vagrant')
call2('vagrant init ubuntu/xenial64')
call2('vagrant up')
