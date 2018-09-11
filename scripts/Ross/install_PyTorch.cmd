@echo off
call _conda.cmd

call activate.bat

conda install pytorch cuda92 -c pytorch -y
pip3 install torchvision
python -m pip install --upgrade pip
