from _shutil import *
import _conda
from _pycharm import pycharm
import webbrowser

PROJECT_NAME = '{{SCRAPY_PROJECT}}'

if call('python -c "import scrapy"') != 0:
    call('conda install scrapy -y')
else:
    print('Scrapy installed already.')

mkdir('~/Projects/scrapy')
chdir('~/Projects/scrapy')

if not exists(PROJECT_NAME):
    call('scrapy startproject %s' % PROJECT_NAME)
    chdir(PROJECT_NAME)
    call('scrapy genspider example example.com')
else:
    chdir(PROJECT_NAME)

replace(f'{PROJECT_NAME}/settings.py', 'ROBOTSTXT_OBEY = True', 'ROBOTSTXT_OBEY = False')
append_line(f'{PROJECT_NAME}/settings.py', "FEED_EXPORT_ENCODING = 'utf-8'")

call('start .')
call([pycharm, getcwd()])
webbrowser.open('https://docs.scrapy.org/en/latest/')