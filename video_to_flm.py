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

fn = glob.glob(locations.video_directory + '*.avi')
json_fn = glob.glob(locations.facial_landmarks_directory + '*.json')
json_fn = [f for f in json_fn if 'analysis' not in f]
np_fn = glob.glob(locations.facial_landmarks_np_directory + '*.npy')

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

def load_video_frames(json_filename):
    if not json_filename: 
        raise ValueError('provide json_filename or video_frames')
    video_frames = json.load(open(json_filename))
    return video_frames

def analyze_facial_landmarks(json_filename = None, video_frames = None):
    if not video_frames: video_frames = load_video_frames(json_filename)
    filename = video_frames[0]['filename']
    c = Counter([frame['success'] for frame in video_frames])
    success, failure = [], []
    for i, frame in enumerate(video_frames):
        if frame['success']: success.append(i)
        else: failure.append(i)
    print(c, filename)
    return c, success, failure

def analyze_all_facial_landmarks(overwrite = False):
    filename = locations.facial_landmarks_directory
    filename += 'facial_landmarks_analysis.json'
    if os.path.isfile(filename) and not overwrite: 
        return json.load(open(filename))
    d = {}
    for f in json_fn:
        if f == filename: continue
        name = f.split('/')[-1].split('.')[0]
        counter,succes,failure = analyze_facial_landmarks(f)
        n_success = counter[True]
        n_failure = counter[False]
        n_frames = n_success + n_failure
        perc_failure = round(n_failure/n_frames*100,2)
        perc_success = round(n_success/n_frames*100,2)
        d[f] = {'n_frames':n_frames,
            'n_success':n_success,
            'perc_success':perc_success,
            'n_failure':n_failure,
            'perc_failure':perc_failure,
            'succes_indices':succes,
            'failure_indices':failure,
            'name':name}
    with open(filename, 'w') as fp:
        json.dump(d,fp)
    return d

def _to_normalized_facial_landmarks(video_frame, normalize = True):
    if not video_frame['success']: return np.zeros(136)
    shape_np = np.array(video_frame['shape_np'])
    matrix= np.array(shape_np)
    if normalize:
        matrix= normalize(matrix, axis=0)
    vector = matrix.ravel()
    return vector


def facial_landmarks_to_np(json_filename = None, video_frames = None,
    save = False, data_type = 'diff'):
    if not video_frames: video_frames = load_video_frames(json_filename)
    filename = video_frames[0]['filename']
    print('processing', filename)
    n_frames = len(video_frames)
    n_features = 136
    X = np.zeros((n_frames, n_features))

    if data_type == 'diff': normalize = False
    else: normalize = True
    for video_frame in video_frames:
        index = video_frame['frame_index']
        X[index] = _to_normalized_facial_landmarks(video_frame, normalize)
                
    if save:
        name = filename.split('/')[-1].split('.')[0]
        filename = locations.facial_landmarks_np_directory + name + '.npy'
        np.save(filename, X)
    return X

    
def write_video():
    '''does not work yet'''
    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  
    # You can use other codecs like 'MJPG' or 'MP4V'
    frame_rate = 30  # Frames per second
    output_filename = 'output_video.avi'  
    # Change the output filename and extension as needed
    frame_size = (width, height)  # Set the frame size (width, height)
    # Create the VideoWriter object
    out = cv2.VideoWriter(output_filename, fourcc, frame_rate, frame_size)
    

