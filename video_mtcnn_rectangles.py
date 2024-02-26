import cv2
from facenet_pytorch import MTCNN
import json
import glob
import locations
import mmcv
import numpy as np
from PIL import Image, ImageDraw 
from PIL.Image import Resampling
import torch

fn = glob.glob(locations.video_directory + '*.avi')
device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

def to_name(filename):
    '''removes path and extension from filename.'''
    return filename.split('/')[-1].split('.')[0]

def analyze_all_videos(filenames = []):
    '''find bounding boxes of the faces in each frame in all videos.'''
    if not filenames: filenames = fn
    n_files = len(filenames)
    for i,filename in enumerate(filenames):
        print('handling video',i,'of',n_files)
        analyze_video(filename)

def analyze_video(filename):
    '''find bounding boxes of the faces in a video for each frame.
    write rectangle coordinates to json file for each frame
    write movie with rectangle superimposed
    '''
    name = to_name(filename)
    print('processing',name)
    video_filename = locations.rectangle_video_directory + name + '_tracked.mp4'
    json_filename = locations.rectangle_json_directory + name + '.json'
    rectangle_frames, rectangles = video_to_rectangle_frames(filename)
    write_video(rectangle_frames, video_filename)
    write_rectangles(rectangles, json_filename)

def load_video(filename):
    '''returns an object to extract frames from a video.'''
    video = mmcv.VideoReader(filename)
    return video

def preprocess_frame(frame):
    '''Map the video frame to the right format with cv2 and PIL.
    '''
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    frame = Image.fromarray(frame)
    return frame

def get_frame_from_video(video):
    '''get the next frame from a video.'''
    frame = next(video)
    frame = preprocess_frame(frame)
    return frame

def get_all_frames_from_video(video):
    '''
    load and preprocess all frames from a video.
    this is very memory hungry ~ 20GB for 15 minutes
    '''
    frames = []
    for frame in video:
        frame = preprocess_frame(video)
        frames.append( frame )
    return frames

def show_frame(frame):
    '''show a specific frame.'''
    plt.ion()
    plt.imshow(frame)
    plt.show()

def frame_to_mtcnn_rectangles(frame):
    '''detect faces in a frame using MTCNN.
    returns a list of bounding boxes and a list of probabilities.'''
    mtcnn = MTCNN(keep_all=True, device=device)
    boxes, probs = mtcnn.detect(frame)
    if type(boxes) == type(None): 
        boxes = []
        probs = []
    else:
        boxes = boxes.tolist()
        probs = probs.tolist()
    return boxes, probs

def draw_rectangles_on_frame(frame, boxes):
    '''draw the face bounding boxes on a frame.'''
    frame_draw = frame.copy()
    draw = ImageDraw.Draw(frame_draw)
    for box in boxes:
        draw.rectangle(box, outline=(255, 0, 0), width=6)
    return frame_draw

def video_to_rectangle_frames(filename):
    '''for each frame in a video, find the face bounding boxes of the faces.
    return a list of frames with the bounding boxes superimposed,
    and a list of dictionaries with the bounding boxes and probabilities.
    '''
    video = load_video(filename)
    rectangle_frames = []
    rectangles = []
    for i, frame in enumerate(video):
        if i > 0 and i % 1000 == 0:print(i, filename)
        frame = preprocess_frame(frame)
        boxes, probs = frame_to_mtcnn_rectangles(frame)
        d ={'filename':filename,
            'frame_index': i, 
            'boxes': boxes, 
            'probs': probs}
        frame_draw = draw_rectangles_on_frame(frame, boxes)
        frame_draw = frame_draw.resize((90, 144), Resampling.BILINEAR)
        rectangle_frames.append(frame_draw)
        rectangles.append(d)
    return rectangle_frames, rectangles

def write_video(rectangle_frames, output_filename):
    '''write a video with the face bounding boxes superimposed.'''
    dim = rectangle_frames[0].size
    fourcc = cv2.VideoWriter_fourcc(*'FMP4')
    video_tracked = cv2.VideoWriter(output_filename,fourcc, 25.0, dim)
    for frame in rectangle_frames:
        video_tracked.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
    video_tracked.release()

def write_rectangles(rectangles, output_filename):
    '''write the face bounding boxes to a json file.'''
    with open(output_filename, 'w') as f:
        json.dump(rectangles, f)

