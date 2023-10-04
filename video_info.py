import glob
import handle_phrases as hp
import json
import locations
import numpy as np
import os

def make_video_infos(tables = None):
    if not tables: tables = hp.Tables()
    fn = glob.glob(locations.video_directory + '*.avi')
    d = {}
    for f in fn:
        file_id = f.split('/')[-1].split('.')[0]
        d[f] = info(file_id, tables)
    return d

class info:
    def __init__(self,file_id, tables = None):
        self.tables = tables
        self.file_id = file_id
        self.name = self.file_id.replace('Crop_','')
        self.name = self.name.replace('_mp3lame','')
        self.name = self.name.replace('_mp3','')
        self.filename_video = locations.video_directory + file_id + '.avi'
        self.filename_json = locations.video_info + file_id + '.json'
        self.filename_np = locations.facial_landmarks_np_directory
        self.filename_np += file_id + '.npy'
        self.d = json.load(open(self.filename_json,'r'))
        self.streams = self.d['streams'][0]
        self._set_info()

    def __repr__(self):
        m = self.name + ' ' + str(round(self.duration,2))
        m += ' ' + str(self.n_frames)
        return m

    def _set_info(self):
        self.height = self.streams['height']
        self.width = self.streams['width']
        self.frame_rate = self.streams['r_frame_rate']
        self.frame_rate = int(self.frame_rate.split('/')[0])
        self.frame_duration = 1/self.frame_rate
        self.duration = float(self.streams['duration'])
        self.n_frames = int(self.streams['nb_frames'])
        self.format = self.d['format']['format_name']

    def frame_index_to_time(self,frame_index):
        return frame_index*self.frame_duration

    def frame_index_to_speech_status(self,frame_index):
        for start,end in self.speech_frames:
            if frame_index >= start and frame_index < end: return True
        return False

    @property
    def table(self):
        if hasattr(self,'_table'): return self._table
        self.number = _name_to_integer(self.name)
        for table in self.tables.tables:
            table_number = _name_to_integer(table.identifier)
            if self.number == table_number:
                self._table = table
                return self._table

    @property
    def speaker(self):
        if hasattr(self,'_speaker'): return self._speaker
        table = self.table
        if not table: raise ValueError('table not found',self.name)
        self.speaker_id = self.name.split(str(self.number))[-1]
        if self.speaker_id == self.table.speakers[0].id:
            self._speaker = self.table.speakers[0]
        elif self.speaker_id == self.table.speakers[1].id:
            self._speaker = self.table.speakers[1]
        else: raise ValueError('speaker not found',self.speaker_id)
        return self._speaker

    @property
    def turns(self):
        if hasattr(self,'_turns'): return self._turns
        self._turns = self.table.speaker_turn_dict[self.speaker.id]
        for turn in self._turns:
            turn.start_frame = round(turn.start_time/self.frame_duration)
            turn.end_frame = round(turn.end_time/self.frame_duration)
        return self._turns

    @property
    def speech_frames(self):
        if hasattr(self,'_speech'): return self._speech_frames
        self._speech_frames = []
        for turn in self.turns:
            self._speech_frames.append((turn.start_frame, turn.end_frame))
        return self._speech_frames

    @property
    def no_speech_frames(self):
        if hasattr(self,'_no_speech_frames'): return self._no_speech_frames
        self._no_speech_frames = []
        for i,turn in enumerate(self.turns):
            if i == 0 and turn.start_time > 0: 
                start_frame = 0
                end_frame = turn.start_frame
                self._no_speech_frames.append((start_frame,end_frame))
                continue
            if i == len(self.turns)-1:
                if turn.end_time < self.duration:
                    start_frame = turn.end_frame
                    end_frame = self.n_frames
                    self._no_speech_frames.append((start_frame,end_frame))
                continue
            start_frame = turn.end_frame
            end_frame = self.turns[i+1].start_frame
            self._no_speech_frames.append((start_frame,end_frame))
        return self._no_speech_frames

    @property
    def X(self):
        if hasattr(self,'_X'): return self._X
        self._X = np.load(self.filename_np)
        return self._X

    @property
    def y(self):
        if hasattr(self,'_y'): return self._y
        self._y = np.zeros(self.n_frames)
        for index in range(self.n_frames):
            if self.frame_index_to_speech_status(index): 
                self._y[index] = 1
            else:
                self._y[index] = 0
        return self._y

        
            
            

def _make_video_info_json(video_dir=locations.video_directory,ext = '.avi'):
    '''create information text for video files in a given directory.'''
    fn = glob.glob(video_dir + '*' + ext)
    directory = locations.video_info 
    for f in fn:
        file_id = f.split('/')[-1].split('.')[0]
        print(file_id)
        cmd = 'ffprobe -v quiet -print_format json -show_format '
        cmd += '-show_streams ' + f + ' > ' + directory + file_id +'.json'
        print(cmd)
        os.system(cmd)


def _name_to_integer(name):
    '''convert a name to an integer'''
    number = ''.join([char for char in name if char.isdigit()])
    return int(number)

