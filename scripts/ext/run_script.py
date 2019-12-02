from _script import *

script_file = get_files()[0]
create_script_link(script_file)
run_script(script_file, overwrite_meta={'template': False})
