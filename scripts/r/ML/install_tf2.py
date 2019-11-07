from _shutil import *

call_echo('conda install tensorflow-gpu -y')

# call_echo('pip install "tensorflow>=2.0.0"')
# call_echo('pip install matplotlib')
call_echo('pip install --upgrade tensorflow-hub')
call_echo('pip install pillow')
call_echo('pip install pandas')
# call_echo('pip install scipy')


# Jupyter
call_echo('conda install jupyter -y')
call_echo('conda install -c conda-forge jupyter_contrib_nbextensions -y')

# https://github.com/ipython-contrib/jupyter_contrib_nbextensions
call_echo('jupyter contrib nbextension install --user')
call_echo('jupyter nbextension enable code_prettify/autopep8')
