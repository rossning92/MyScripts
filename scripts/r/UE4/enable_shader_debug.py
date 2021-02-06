from _shutil import *

# https://docs.unrealengine.com/en-us/Programming/Rendering/ShaderDevelopment
# Use Ctrl+Shift+. to recompile shaders
append_line(r"{{UE_SOURCE}}\Engine\Config\ConsoleVariables.ini",
            'r.ShaderDevelopmentMode=1')
