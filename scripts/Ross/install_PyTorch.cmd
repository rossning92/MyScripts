@echo off
call _conda.cmd

conda install pytorch cuda92 -c pytorch
pip3 install torchvision
python -m pip install --upgrade pip
