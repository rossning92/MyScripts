from _shutil import *

call_echo('conda install jupyter -y')
call_echo('conda install -c conda-forge jupyter_contrib_nbextensions -y')

# https://github.com/ipython-contrib/jupyter_contrib_nbextensions
call_echo('jupyter contrib nbextension install --user')
call_echo('jupyter nbextension enable code_prettify/autopep8')
call_echo('pip install --upgrade autopep8')
