from _shutil import cd
from ext.run_script_ssh import pull_file_putty

src = r"{{_SRC_FILE}}"

cd("~/Desktop")

pull_file_putty(src)
