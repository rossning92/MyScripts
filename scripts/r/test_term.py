from _term import *

lines = ['Hello %s' % i for i in range(10)]
lw = ListWidget(lines=lines, text_changed=lambda t: None, item_selected=lambda i: None)

lw.exec()
