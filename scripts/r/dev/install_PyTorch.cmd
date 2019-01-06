@echo off
set "PATH=C:\tools\miniconda3;C:\tools\miniconda3\Scripts;%PATH%"

:: call activate.bat

conda install pytorch cuda92 -c pytorch -y
pip install torchvision
python -m pip install --upgrade pip
