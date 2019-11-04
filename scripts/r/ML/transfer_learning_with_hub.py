from __future__ import absolute_import, division, print_function, unicode_literals
import matplotlib.pylab as plt
import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.keras import layers
import numpy as np
import PIL.Image as Image
import tensorflow.keras as keras

# classifier_url = "https://tfhub.dev/google/tf2-preview/mobilenet_v2/classification/2"  # @param {type:"string"}
#
# IMAGE_SHAPE = (224, 224)
#
# classifier = tf.keras.Sequential([
#     hub.KerasLayer(classifier_url, input_shape=IMAGE_SHAPE + (3,))
# ])


data_root = tf.keras.utils.get_file(
    'flower_photos', 'https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz',
    untar=True)
directory = str(data_root)


image_generator = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1 / 255)

directory = r'C:\tmp\cont'
IMAGE_SHAPE = (224, 224)
image_data = image_generator.flow_from_directory(directory, target_size=IMAGE_SHAPE)
for image_batch, label_batch in image_data:
    print("Image batch shape: ", image_batch.shape)
    print("Label batch shape: ", label_batch.shape)
    break

feature_extractor_url = "https://tfhub.dev/google/tf2-preview/mobilenet_v2/feature_vector/2"  # @param {type:"string"}
feature_extractor_layer = hub.KerasLayer(feature_extractor_url,
                                         input_shape=(224, 224, 3))
feature_batch = feature_extractor_layer(image_batch)

feature_extractor_layer.trainable = False

# Attach a classification head
model = tf.keras.Sequential([
    feature_extractor_layer,
    layers.Dense(image_data.num_classes, activation='softmax')
])

print(model.summary())

predictions = model(image_batch)
model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss='categorical_crossentropy',
    metrics=['acc'])


class CollectBatchStats(tf.keras.callbacks.Callback):
    def __init__(self):
        self.batch_losses = []
        self.batch_acc = []

    def on_train_batch_end(self, batch, logs=None):
        self.batch_losses.append(logs['loss'])
        self.batch_acc.append(logs['acc'])
        self.model.reset_metrics()


steps_per_epoch = np.ceil(image_data.samples / image_data.batch_size)

batch_stats_callback = CollectBatchStats()

tensorboard_callback = keras.callbacks.TensorBoard()
history = model.fit_generator(image_data, epochs=10,
                              steps_per_epoch=steps_per_epoch,
                              callbacks=[batch_stats_callback, tensorboard_callback])

#
#
# plt.figure()
# plt.ylabel("Loss")
# plt.xlabel("Training Steps")
# plt.ylim([0, 2])
# plt.plot(batch_stats_callback.batch_losses)
#
# plt.figure()
# plt.ylabel("Accuracy")
# plt.xlabel("Training Steps")
# plt.ylim([0, 1])
# plt.plot(batch_stats_callback.batch_acc)
#
# """### Check the predictions
#
# To redo the plot from before, first get the ordered list of class names:
# """
#
# class_names = sorted(image_data.class_indices.items(), key=lambda pair: pair[1])
# class_names = np.array([key.title() for key, value in class_names])
# class_names
#
# """Run the image batch through the model and convert the indices to class names."""
#
# predicted_batch = model.predict(image_batch)
# predicted_id = np.argmax(predicted_batch, axis=-1)
# predicted_label_batch = class_names[predicted_id]
#
# """Plot the result"""
#
# label_id = np.argmax(label_batch, axis=-1)
#
# plt.figure(figsize=(10, 9))
# plt.subplots_adjust(hspace=0.5)
# for n in range(30):
#     plt.subplot(6, 5, n + 1)
#     plt.imshow(image_batch[n])
#     color = "green" if predicted_id[n] == label_id[n] else "red"
#     plt.title(predicted_label_batch[n].title(), color=color)
#     plt.axis('off')
# _ = plt.suptitle("Model predictions (green: correct, red: incorrect)")
