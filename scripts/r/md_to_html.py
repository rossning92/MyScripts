from _shutil import *


in_file = get_files(cd=True)[0]
out_file = os.path.splitext(in_file)[0] + ".html"

call_echo(["pandoc", "-s", "-c", "pandoc.css", in_file, "-o", out_file])
shell_open(out_file)
