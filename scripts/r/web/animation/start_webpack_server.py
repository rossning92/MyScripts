from _shutil import *

cd('_threejs')

setup_nodejs()
project_path = r'{{ANIMATION_PROJECT_PATH}}' if r'{{ANIMATION_PROJECT_PATH}}' else None

if not os.path.exists('node_modules'):
    call_echo('yarn install')

args = os.path.join('node_modules', '.bin', 'webpack-dev-server')

if project_path:
    args += ' --env.entryFolder="%s"' % project_path
    copy('pages/', project_path + '/')

args += ' --open --watch'

call_echo(args)
