from _shutil import *
import xml.etree.ElementTree as ET
import configparser

# Notepad++
config_file = expandvars('%APPDATA%/Notepad++/config.xml')
if exists(config_file):
    print('Config Notepad++...')
    tree = ET.parse(config_file)
    root = tree.getroot()

    node = root.findall(".//GUIConfig[@name='RememberLastSession']")[0]
    node.text = 'no'

    tree.write(config_file)

# Sumatra
config_file = r"C:\ProgramData\chocolatey\lib\sumatrapdf.commandline\tools\SumatraPDF-settings.txt"
if exists(config_file):
    print('Config SumatraPdf...')
    replace(config_file, 'RememberOpenedFiles = .*', 'RememberOpenedFiles = false', debug_output=True)
    replace(config_file, 'UseTabs = .*', 'UseTabs = false', debug_output=True)

# Everything
config_file = r"C:\Users\Ross\AppData\Roaming\Everything\Everything.ini"
if exists(config_file):
    print('Config Everything...')
    config = configparser.ConfigParser()
    config.read(config_file)

    config['Everything']['show_window_key'] = '577'

    with open(config_file, 'w') as f:
        config.write(f)
