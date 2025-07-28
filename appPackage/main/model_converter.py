# from tensorflow.keras.models import load_model  # type: ignore
# import tensorflow as tf

# model = load_model("Model/xception_cervical_cancer.keras")


# # Convert to TensorFlow Lite
# converter = tf.lite.TFLiteConverter.from_keras_model(model)
# tflite_model = converter.convert()

# # Save the .tflite model
# try:
#     with open("Model/xception_cervical_cancer_model.tflite", "wb") as f:
#         f.write(tflite_model)
#         print("successfully converted")
# except Exception as e:
#     print(f"Error saving the model: {str(e)}")
