from _term import *

lines = ['Hello %s' % i for i in range(10)]
w = FilterWindow('ping 127.0.0.1 -t')

print_color('Hello')
