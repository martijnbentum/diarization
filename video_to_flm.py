import cv2
import dlib
import locations
from matplotlib import pyplot as plt
import numpy as np

def load_video(filename):
    return cv2.VideoCapture(filename)

def load_image_from_video(video):
    success, image = video.read()
    return success, image

def image_to_grayscale(image):
    return cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)

def show_image(image, title = ''):
    cv2.imshow(title, image)

def get_frontal_face_detector():
    return dlib.get_frontal_face_detector()

def get_facial_landmark_predictor(model_filename = None):
    if not model_filename: model_filename = locations.face_landmarks_filename
    predictor = dlib.shape_predictor(model_filename)
    return predictor

def get_face_rectangle(image, detector = None):
    if not detector: detector = get_frontal_face_detector()
    rects = detector(image)
    assert len(rects) == 1
    return rects[0]

def get_facial_landmarks(image, rectangle = None, predictor = None):
    if not rectangle: rectangle = get_face_rectangle(image)
    if not predictor: predictor = get_facial_landmark_predictor()
    shape = predictor(image,rectangle)
    shape_np = np.zeros((68,2), dtype = 'int')
    for i in range(68):
        shape_np[i] = shape.part(i).x, shape.part(i).y
    return shape_np, shape

def rectangle_to_tuples(rectangle):
    p1 = rectangle.tl_corner()
    p1 = p.x, p.y
    p2 = rectangle.br_corner()
    p2 = p.x, p.y
    return p1, p2

def add_landmarks_to_image(image, shape_np, rectangle):
    for i, (x,y) in enumerate(shape_np):
        cv2.circle(image, (x,y), 1, (0,0,255), -1)

def handle_video_frame(video, detector = None, predictor = None, 
    add_to_image = True):
    succes, image = load_image_from_video(video)
    if not succes: 
        print('could not load fram from video')
        return
    gray = image_to_grayscale(image)
    rectangle = get_face_rectangle(image, detector)
    shape_np, shape = get_facial_landmarks(gray, rectangle, predictor)
    if add_to_image: add_landmarks_to_image(image,shape_np,rectangle)
    return image, gray, rectangle, shape_np, shape

def handle_video(filename, detector = None, predictor = None):
    if not detector: detector = get_frontal_face_detector()
    if not predictor: predictor= get_facial_landmark_predictor()
    video = load_video(filename)
    
