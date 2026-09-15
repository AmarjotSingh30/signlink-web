import tensorflow as tf
from keras.models import model_from_json

print("Loading original model...")
# 1. Load the original Keras model
with open("model/model-mp.json", "r") as f:
    model_json = f.read()

model = model_from_json(model_json)
model.load_weights("model/model-mp.h5")

print("Converting to TFLite...")
# 2. Convert to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# 3. Save the ultra-lightweight file
with open("model/model-mp.tflite", "wb") as f:
    f.write(tflite_model)

print("SUCCESS: Compressed model saved as model/model-mp.tflite!")