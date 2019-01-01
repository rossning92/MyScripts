from _shutil import *
import _conda

chdir('~/Projects/scrapy/{{SCRAPY_PROJECT}}')

# url = get_clip()
# if not url.startswith('http'):
#    raise Exception('URL is not in clipboard.')

call('scrapy shell %s' % r'{{SCRAPY_URL}}')
