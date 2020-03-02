from _shutil import *

cd('_threejs')

setup_nodejs()

if not os.path.exists('node_modules'):
    call_echo('yarn install')

dev_server = os.path.join('node_modules', '.bin', 'webpack-dev-server')
args = r'%s --env.entryFolder="{{ANIMATION_PROJECT_PATH}}" --open --watch' % dev_server
call_echo(args)
