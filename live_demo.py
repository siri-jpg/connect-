import os
import cv2
import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

label_lines = [line.rstrip() for line in tf.io.gfile.GFile("training_set_labels.txt")]

with tf.io.gfile.GFile("trained_model_graph.pb", 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    _ = tf.import_graph_def(graph_def, name='')

sess = tf.Session()
softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')


def predict(image_data):
    resized_image = image_data[70:350, 70:350]
    resized_image = cv2.resize(resized_image, (200, 200))
    image_bytes = cv2.imencode('.jpg', resized_image)[1].tobytes()

    predictions = sess.run(
        softmax_tensor,
        {'DecodeJpeg/contents:0': image_bytes}
    )

    max_index = np.argmax(predictions[0])
    result = label_lines[max_index]
    confidence = predictions[0][max_index]

    return result, confidence