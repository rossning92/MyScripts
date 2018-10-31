import os
import sys
from selenium import webdriver

# sys.path.insert(0, r'E:\bin\selenium')

chrome_profile = os.environ['LOCALAPPDATA'] + '\\Google\\Chrome\\User Data\\Default'
#print(chrome_profile)
chrome_profile = 'C:\\ChromeProfile'

options = webdriver.ChromeOptions()
options.add_argument('user-data-dir=%s' % chrome_profile)  # Path to your chrome profile
w = webdriver.Chrome(chrome_options=options)
