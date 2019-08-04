@echo off
set "PATH=C:\tools\Anaconda3\Scripts;C:\tools\miniconda3\Scripts;%PATH%"
call activate.bat

conda install pytorch torchvision cudatoolkit=9.0 -c pytorch -y
