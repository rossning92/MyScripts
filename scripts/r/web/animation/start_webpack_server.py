from _shutil import *


setup_nodejs()
project_path = r'{{ANIMATION_PROJECT_PATH}}' if r'{{ANIMATION_PROJECT_PATH}}' else None

cd('_threejs')
if not os.path.exists('node_modules'):
    call_echo('yarn install')
    call_echo('yarn link')

cd(project_path)
call_echo('yarn link yo')
os.environ['ENTRY_FOLDER'] = project_path
script = os.path.join('node_modules', 'yo', 'bin', 'start-app.js')
call_echo(['node', script])
