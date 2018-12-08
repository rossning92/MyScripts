from os import environ, pathsep

# Prepend anaconda to PATH
environ["PATH"] = pathsep.join([
    r'C:\tools\miniconda3',
    r'C:\tools\miniconda3\Scripts'
]) + pathsep + environ["PATH"]