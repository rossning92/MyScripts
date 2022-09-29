from _shutil import call_echo, cd, setup_nodejs

setup_nodejs()


cd("~/.vscode/extensions")

call_echo("npm install -g yo generator-code")
call_echo("yo code")
