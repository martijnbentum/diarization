'''
module to handle ifadv meta data regarding speakers and recordings.
'''

import glob
import ifadv_clean
import locations
import string
import os

fn_wav = glob.glob(locations.ifadv_wav_directory+ '*.wav')

def make_recording(wav_filename):
    '''create a recording object based on the wav filename.'''
    number = _wav_filename_to_number(wav_filename)
    for line in open_recording_file():
        if line[0] == number:
            return Recording(line)
    raise ValueError(wav_filename, 'could not find recording metadata')
    

def open_recording_file(f = locations.recording_data_filename):
    '''open file with metadata for all recordings.'''
    if not os.path.exists(f):
        f = '../' + f.split('/')[-1] 
    return open_file(f)

def open_speaker_file(f = locations.speaker_data_filename):
    '''open file with metadata for all speakers.'''
    if not os.path.exists(f):
        f = '../' + f.split('/')[-1] 
    return open_file(f)

def open_file(f):
    '''open a tab separated file with ifadv meta data.'''
    with open(f) as fin:
        t = fin.read().split('\n')
    return [line.split('\t') for line in t]


class Speaker:
    '''show metadata for an ifadv speaker. 
    links a speaker to all recordings they speak in'''
    def __init__(self, line): 
        self.line = line
        self._set_info()
        self._add_recordings()
    
    def __repr__(self):
        m = self.id + ' - '
        m += self.sex + ' - '
        m += str(self.age)
        return m 
        
    def _set_info(self):
        sex = 'female' if self.line[0] =='F' else 'male'
        self.sex = sex
        self.age = int(self.line[1])
        self.id = self.line[2]

    def _add_recordings(self):
        self.recordings = []
        for line in open_recording_file():
            if line[2] == self.id or line[3] == self.id:
                self.recordings.append(Recording(line))


class Recording:
    '''show metadata for an IFADV recording and links to speakers on 
    channel 1 and 2.
    '''
    def __init__(self, line):
        self.line = line
        self._set_info()

    def __repr__(self):
        m = self.id_name + ' | ch1: ' 
        m += self.speaker_ch1.__repr__() + ' | ch2: '
        m += self.speaker_ch2.__repr__()  
        return m

    def _set_info(self):
        self.id_number = int(self.line[0])
        self.wav_filename = _get_wav_filename(self.id_number)
        self.id_name = self.wav_filename.split('/')[-1].split('.')[0]
        self.speaker_id_ch1 = self.line[2]
        self.speaker_id_ch2 = self.line[3]

    def channel_to_speaker(self, channel):
        '''return speaker object corresponding to a specific channel.'''
        if channel == 1: return self.speaker_ch1
        if channel == 2: return self.speaker_ch2
        raise ValueError(channel, 'choose channel 1 or 2')

    @property
    def speaker_ch1(self):
        '''return speaker object corresponding to channel 1 (left).'''
        if hasattr(self,'_speaker_ch1'): return self._speaker_ch1
        self._speaker_ch1 = _get_speaker(self.line[2])
        return self._speaker_ch1

    @property
    def speaker_ch2(self):
        '''return speaker object corresponding to channel 2 (right).'''
        if hasattr(self,'_speaker_ch2'): return self._speaker_ch2
        self._speaker_ch2 = _get_speaker(self.line[3])
        return self._speaker_ch2

def _wav_filename_to_number(wav_filename):
    '''get the filenumber based on the ifadv wav filename.'''
    number = ''
    f = wav_filename.split('/')[-1].split('.')[0]
    for char in f:
        if char in string.ascii_uppercase: continue
        number += char
    return number
        

def _get_wav_filename(record_id_number):
    '''get the wav filename for an ifadv recording based on the record 
    id number.
    '''
    id_number = str(record_id_number)
    for filename in fn_wav:
        number = _wav_filename_to_number(filename)
        if id_number == number: return filename
    raise ValueError(id_number,'no file found with this number')

def _get_speaker(speaker_id):
    '''return speaker object based on ifadv speaker id.'''
    for line in open_speaker_file():
        if line[2] == speaker_id: return Speaker(line)
    raise ValueError(speaker_id,'could not find this speaker id')
            
        
