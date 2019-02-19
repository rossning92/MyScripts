from _shutil import *
import xml.etree.ElementTree as ET

# Notepad++
config = expandvars('%APPDATA%/Notepad++/config.xml')
tree = ET.parse(config)
root = tree.getroot()

node = root.findall(".//GUIConfig[@name='RememberLastSession']")[0]
node.text = 'no'

tree.write(config)
