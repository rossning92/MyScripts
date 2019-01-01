from _shutil import *
import _conda

chdir('~/Projects/scrapy/{{SCRAPY_PROJECT}}')

remove('output.json')
call('scrapy crawl example -o output.json', highlight={
    '\(200\)': 'green',
    '^\w+?Error:': 'RED', 'ERROR': 'RED',
})
