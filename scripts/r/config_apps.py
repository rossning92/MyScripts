from _shutil import *
import xml.etree.ElementTree as ET

# Notepad++
config_file = expandvars('%APPDATA%/Notepad++/config.xml')
tree = ET.parse(config_file)
root = tree.getroot()

node = root.findall(".//GUIConfig[@name='RememberLastSession']")[0]
node.text = 'no'

tree.write(config_file)

# Sumatra
config_file = r"C:\ProgramData\chocolatey\lib\sumatrapdf.commandline\tools\SumatraPDF-settings.txt"
replace(config_file, 'RememberOpenedFiles = .*', 'RememberOpenedFiles = false', debug_output=True)
replace(config_file, 'UseTabs = .*', 'UseTabs = false', debug_output=True)
