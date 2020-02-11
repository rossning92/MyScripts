from _android import *

logcat(filter_str=re.escape(r'{{_FILTER}}'),
       proc_name=r'{{_PROC_NAME}}')
