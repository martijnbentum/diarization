from collections import Counter
import cv2
import dlib
import glob
import json
import locations
from matplotlib import pyplot as plt
import numpy as np
import os
from sklearn.preprocessing import normalize

def get_facial_landmark_predictor(model_filename = None):
    if not model_filename: model_filename = locations.face_landmarks_filename
    predictor = dlib.shape_predictor(model_filename)
    return predictor

def get_facial_landmarks(image, rectangle = None, predictor = None):
    if not rectangle: rectangle = get_face_rectangle(image)
    if not predictor: predictor = get_facial_landmark_predictor()
    shape = predictor(image,rectangle)
    shape_np = np.zeros((68,2), dtype = 'int')
    for i in range(68):
        shape_np[i] = shape.part(i).x, shape.part(i).y
    return shape_np, shape
