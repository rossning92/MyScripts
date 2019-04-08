from _shutil import *

# from _conda import *

# https://www.tensorflow.org/hub/tutorials/image_retraining

TRAIN_IMG_DIR = r'{{TRAIN_IMG_DIR}}'
TRAINING_STEPS = 4000

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
if True:
    download('https://github.com/tensorflow/hub/raw/master/examples/image_retraining/retrain.py')
    exec_bash(rf'''python retrain.py \
--image_dir {TRAIN_IMG_DIR} \
--tfhub_module https://tfhub.dev/google/imagenet/mobilenet_v2_035_224/classification/2 \
--how_many_training_steps {TRAINING_STEPS}''')


download('https://github.com/tensorflow/tensorflow/raw/master/tensorflow/examples/label_image/label_image.py')
exec_bash(r'''python label_image.py \
--graph=/c/tmp/output_graph.pb --labels=/c/tmp/output_labels.txt \
--input_layer=Placeholder \
--output_layer=final_result \
--image=paper.jpg \
--input_width 224 \
--input_height 224''')