from _shutil import *

# from _conda import *

# https://www.tensorflow.org/hub/tutorials/image_retraining

PROJ = expanduser('~/image_retraining')
mkdir(PROJ)
chdir(PROJ)

if not exists('flower_photos'):
    exec_bash('''set -e
    curl -LO http://download.tensorflow.org/example_images/flower_photos.tgz
    tar xzf flower_photos.tgz
    ''')

# Requirement
# https://www.tensorflow.org/hub/installation
call('pip install "tensorflow>=1.7.0"')
call('pip install tensorflow-hub')

# Retrain
if False:
    download('https://github.com/tensorflow/hub/raw/master/examples/image_retraining/retrain.py')
    call('python retrain.py --image_dir flower_photos')


download('https://github.com/tensorflow/tensorflow/raw/master/tensorflow/examples/label_image/label_image.py')
exec_bash(r'''python label_image.py \
--graph=tmp/output_graph.pb --labels=tmp/output_labels.txt \
--input_layer=Placeholder \
--output_layer=final_result \
--image=flower_photos/daisy/21652746_cc379e0eea_m.jpg''')