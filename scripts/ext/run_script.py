from _script import *

script_file = get_files()[0]
create_script_link(script_file)

meta_file = os.path.abspath(os.path.splitext(script_file)[0] + '.yaml')
meta = get_script_meta(meta_file)
meta['template'] = False
save_meta_file(meta, meta_file)

run_script(script_file)
