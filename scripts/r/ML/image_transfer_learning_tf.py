from _shutil import *

# from _conda import *

# https://www.tensorflow.org/hub/tutorials/image_retraining

TRAIN_IMG_DIR = r'{{TRAIN_IMG_DIR}}'
TRAINING_STEPS = 4000

PROJ = expanduser('~/Projects/image_retraining')

make_and_change_dir(PROJ)

if not exists('flower_photos'):
    exec_bash('''set -e
    curl -LO http://download.tensorflow.org/example_images/flower_photos.tgz
    tar xzf flower_photos.tgz
    ''')

# Requirement
# https://www.tensorflow.org/hub/installation
if wait_key('install tensoflow?'):
    call_echo('pip uninstall tensorflow')
    call_echo('pip install "tensorflow==1.14"')  # Only 1.14 support GPU
    # call_echo('pip install "tensorflow>=2.0.0"')
    call_echo('pip install --upgrade tensorflow-hub')

# Retrain
if True:
    download('https://github.com/tensorflow/hub/raw/master/examples/image_retraining/retrain.py')
    call2('python retrain.py '
          f'--image_dir {TRAIN_IMG_DIR} '
          '--tfhub_module https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/feature_vector/3 '
          f'--how_many_training_steps {TRAINING_STEPS}'
          )

if False:
    download('https://github.com/tensorflow/tensorflow/raw/master/tensorflow/examples/label_image/label_image.py')
    exec_bash(r'''python label_image.py \
    --graph=/c/tmp/output_graph.pb --labels=/c/tmp/output_labels.txt \
    --input_layer=Placeholder \
    --output_layer=final_result \
    --image=paper.jpg \
    --input_width 224 \
    --input_height 224''')
