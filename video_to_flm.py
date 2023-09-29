import cv2
import dlib
import glob
import json
import locations
from matplotlib import pyplot as plt
import numpy as np

fn = glob.glob(locations.video_directory + '*.avi')

def make_all_facial_landmarks_json():
    for f in fn:
        print(f)
        video_frames = handle_video(f)
        facial_landmarks_to_json(video_frames)


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
    assert len(rects) > 0
    if len(rects) > 1: print('more than one face detected')
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
    p1 = p1.x, p1.y
    p2 = rectangle.br_corner()
    p2 = p2.x, p2.y
    return p1, p2

def add_landmarks_to_image(image, shape_np, rectangle):
    for i, (x,y) in enumerate(shape_np):
        cv2.circle(image, (x,y), 1, (0,0,255), -1)
    cv2.rectangle(image, *rectangle_to_tuples(rectangle), (0,255,0), 2)
    

def handle_video_frame(video, detector = None, predictor = None, 
    add_to_image = True):
    succes, image = load_image_from_video(video)
    if not succes: 
        print('could not load fram from video')
        return 'done'
    gray = image_to_grayscale(image)
    try:rectangle = get_face_rectangle(image, detector)
    except AssertionError:
        print('no face detected')
        rectangle, shape_np, shape = None, None, None
    else:
        shape_np, shape = get_facial_landmarks(gray, rectangle, predictor)
    if add_to_image and shape: 
        add_landmarks_to_image(image,shape_np,rectangle)
    return image, gray, rectangle, shape_np, shape

def handle_video(filename, detector = None, predictor = None, 
    store_everything = False):
    if not detector: detector = get_frontal_face_detector()
    if not predictor: predictor= get_facial_landmark_predictor()
    video = load_video(filename)
    video_frames = []
    frame_index = 0
    while True:
        output = handle_video_frame(video, detector, predictor)
        if output == 'done': break
        image, gray, rectangle, shape_np, shape = output
        success = shape is not None
        if store_everything:
            d = {'filename':filename,'frame_index':frame_index,'image':image,
                'gray':gray,'rectangle':rectangle,'shape_np':shape_np,
                'shape':shape,'success':success}
        else:
            if type(shape_np) == type(None): shape_np = []
            else: shape_np = shape_np.tolist()
            d = {'filename':filename,'frame_index':frame_index,
                'shape_np':shape_np,
                'success':success}
        video_frames.append(d)
        frame_index += 1
        if frame_index % 100 == 0: print(frame_index,filename)
    return video_frames

def facial_landmarks_to_json(video_frames, filename = None):
    if not filename: filename = video_frames[0]['filename']
    filename = filename.split('/')[-1].split('.')[0]
    filename = locations.facial_landmarks_directory + filename + '.json'
    json.dump(video_frames, open(filename,'w'))



    

