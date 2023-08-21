import glob
import numpy as np
import scipy.io.wavfile as wav
import soundfile as sf
import scipy.signal as signal
import pickle
import audio_identifier

def pickle_recording(recording, directory = ''):
    f = recording.filename.split('/')[-1].split('.')[0] + '.pickle'
    if directory and os.path.isdir(directory):
        if not directory.endswith('/'): directory += '/'
        f = directory + f
        print('saving in dir:',directory, '\nfilename:',f)
    else:print('saving in local folder',f)
    recording.input_signal = None
    with open(f,'wb') as fout:
        pickle.dump(recording,fout)

def load_pickle_recording(wav_filename = '', directory = '', 
    pickle_filename =''):
    if wav_filename:
        f = wav_filename.split('/')[-1].split('.')[0] + '.pickle'
        if directory and os.path.isdir(directory):
            if not directory.endswith('/'): directory += '/'
            f = directory + f
            print('loading in dir:',directory, '\nfilename:',f)
        else:print('loading in local folder',f)
    elif pickle_filename: f = pickle_filename
    else: raise ValueError('provide wav_filename or pickle_filename')
    with open(f,'rb') as fin:
        recording = pickle.load(fin)
    return recording

class Recordings:
    def __init__(self):
        self.audio_ids = audio_identifier.Audio_ids()
        self.audios = self.audio_ids.audios
        self.microphone_names = 'left_respeaker,minidsp,shure,grensvlak'
        self.microphone_names = self.microphone_names.split(',')
        self._make_recordings()

    def _make_recordings(self):
        self.recordings = []
        for microphone_name in self.microphone_names:
            recording = Recording(microphone_name, self)
            self.recordings.append(recording)

    def _set_audio(self):
        sample_rate, input_signal = load_audio(self.filename)
        self.sample_rate = sample_rate
        self.input_signal = input_signal


    def handle_all_tones(self):
        frequencies = [700,500,300]
        names = ['audio_id','start','end']
        for frequency, name in zip(frequencies,names):
            print('handling',name,frequency)
            self._handle_tones(frequency,name)

    def make_sections(self):
        self.sections = make_sections(self)

    def save(self):
        pickle_recording(self, self.output_directory)

class Recording:
    def __init__(self, microphone_name, recordings):
        self.microphone_name = microphone_name
        self.audio_index = 4
        self.recordings = recordings
        self.audios = self.recordings.audios[self.microphone_name]

    def __repr__(self):
        return 'recording ' + self.microphone_name

    def _find_start(self):
        self.audio_info = list(self.audios.values())[self.audio_index]
        self.wav_filename = self.audio_info.path
        self.sample_rate= self.audio_info.sample_rate
        self.start_audio, sr = sf.read(self.wav_filename, start = 0,
            stop = 300 * self.sample_rate)
        self._handle_tones(500,self.start_audio,'start_tones_timestamps')

    def _handle_tones(self,frequency, audio, name):
        d = {'sample_rate':self.sample_rate,'input_signal':audio,
            'frequency':frequency, 'return_all': True}
        o, ts, m = get_start_end_timestamps(**d)
        setattr(self, name, o)
        self._magnitudes = m
        self._timestamps = ts
        
class Section:
    def __init__(self,audio_id_tones,start_tones,end_tones,
        filename_recording,section_index):
        self.audio_id_tones = audio_id_tones
        self.start_tones = start_tones
        self.end_tones = end_tones
        self.filename_recording = filename_recording
        self.section_index = section_index
        self._set_info()

    def __repr__(self):
        m = 'section| start: '
        m += str(self.start)
        m += ' end: '
        m += str(self.end)
        m += ' dur: '
        m += str(round(self.end - self.start,2))
        m += ' ' + self.filename_recording.split('/')[-1]
        m += ' ' + str(self.section_index)
        return m

    def _set_audio_id(self):
        if not self.audio_id_tones: 
            self.start_audio_id, self.end_audio_id = None, None
            self.audio_ok = False
        self.start_audio_id = self.audio_id_tones[0][1] + 2
        self.end_audio_id = self.audio_id_tones[1][0] - 1
        self.audio_ok = True
 
    def _set_start(self):
        if not self.start_tones: 
            self.start= None
            self.start_ok = False
        self.start = self.start_tones[1][1] + 1
    
    def _set_end(self):
        if not self.end_tones:
            self.end = None
            self.end_ok = False
        self.end = self.end_tones[0][0] -1

    def _set_info(self):
        self._set_audio_id()
        self._set_start()
        self._set_end()


def group_segments(segments, delta = 6):
    found = False
    output = []
    for index,segment in enumerate(segments):
        if index +1 >= len(segments):
            print('no segements left to group with',segement,index)
            continue
        if found == False:
            next_segment =segments[index + 1]
            if next_segment[0] - segment[0] < delta:
                output.append([segment,next_segment])
                found = True
        else: found = False
    print('found pairs',len(output),'n segment',len(segments))
    return output

def find_closest(pair,other_pairs, before = True):
    delta = 10**9
    current_index = None
    for index, other_pair in enumerate(other_pairs):
        v = pair[0][0] - other_pair[0][0]
        if v < 0 and before: continue
        if v > 0 and not before: continue
        v = abs(v)
        if v < delta: 
            current_index = index
            delta = v
    return other_pairs[current_index]
        

def make_sections(recording):
    print('grouping audio id')
    audio_id = group_segments(recording.audio_id)
    print('grouping start')
    start = group_segments(recording.start)
    print('grouping end')
    end= group_segments(recording.end)
    sections = []
    for index,start_tones in enumerate(start):
        end_tones = find_closest(start_tones,end, False)
        audio_id_tones = find_closest(start_tones,audio_id, True)
        s = Section(audio_id_tones,start_tones,end_tones,recording.filename,
            index)
        sections.append(s)
    return sections

def load_audio(filename):
    try:
        sample_rate, audio_data = wav.read(filename)
    except ValueError:
        audio_data, sample_rate = sf.read(filename)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 1]
    return sample_rate, audio_data

def get_start_end_timestamps(filename = None, sample_rate = None, 
    input_signal = None, frequency = 500, return_all = False):
    d = {'filename':filename,'sample_rate':sample_rate,
        'input_signal':input_signal,'frequency':frequency}
    sr, magnitudes= sliding_window_with_hamming(**d)
    threshold = _find_threshold(magnitudes)
    timestamps = _get_timestamps(sr, magnitudes)
    output = []
    index = 0
    while True:
        try:
            start, end, index = find_segment(magnitudes, index, threshold)
        except: 
            index +=1
        else:
            if start and end:
                output.append([timestamps[start]-0.4, timestamps[end]-0.4])
        if index == None or index >= len(magnitudes): break
    if return_all: return output, timestamps, magnitudes
    return output

def sliding_window_with_hamming(filename = None, sample_rate = None,
    input_signal = None, frequency = 500, window_size_ms = 500):
    if filename == sample_rate == input_signal == None:
        raise ValueError('provide filename or sample_rate & input_signal')
    if type(input_signal) == type(None):
        sample_rate, input_signal = load_audio(filename)
    window_size = int(window_size_ms / 1000 * sample_rate)
    hop_size = window_size // 2
    output_sample_rate = 1000 / (window_size_ms / 2)
    output_signal = []
    padded_signal = np.pad(input_signal, window_size, mode = 'reflect')
    window = signal.windows.hamming(window_size)
    for i in range(0, len(input_signal), hop_size):
        frame = padded_signal[i:i + window_size]
        windowed_frame = frame * window
        m = get_magnitude_at_frequency(frequency, windowed_frame,sample_rate)
        output_signal.append( m )
    return output_sample_rate, output_signal

def fft(audio_data):
    return np.fft.fft(audio_data)

def magnitude_spectrum(fft_data):
    return np.abs(fft_data)

def get_magnitude_at_frequency(frequency, audio_data, sample_rate):
    index = int(frequency * len(audio_data) / sample_rate)
    fft_data = fft(audio_data)
    ms = magnitude_spectrum(fft_data)
    return ms[index]

def find_segment(magnitudes, start_index, threshold):
    start_tone_index = find_start(start_index, magnitudes,threshold)
    if start_tone_index == None: return None, None,None 
    if start_tone_index == len(magnitudes) -1: return None, None,None 
    end_tone_index = find_end(start_tone_index +1, magnitudes, threshold)
    if end_tone_index == None: 
        return start_tone_index, len(magnitudes) -1,None 
    return start_tone_index, end_tone_index, end_tone_index+1

def find_start(start_index, samples, threshold):
    _check_conditions(start_index, samples, threshold, 'start')
    for i in range(start_index, len(samples)):
        if samples[i] > threshold: return i
    return None

def find_end(start_index, samples, threshold):
    _check_conditions(start_index, samples, threshold, 'end')
    for i in range(start_index, len(samples)):
        if samples[i] < threshold: return i
    return None



def _check_conditions(index, samples, threshold,condition_type):
    if index >= len(samples): 
        raise ValueError('index is outside samples', index, 
            len(samples))
    if condition_type == 'start' and samples[index] > threshold:
        if index == 0: return
        raise ValueError('value at', index, 'should be lower than', 
            threshold, 'is: ', samples[index])
    if condition_type == 'end' and samples[index] < threshold:
        raise ValueError('value at', index, 'should be higher than', 
            threshold, 'is: ', samples[index], threshold-samples[index])
    
def _get_timestamps(sr, samples):
    increments = 1/ sr
    timestamps = [round(i *increments,4) for i in range(len(samples))]
    return timestamps

def _find_threshold(samples):
    median = np.median(samples)
    maximum = np.max(samples)
    threshold = (maximum*1.5 + median)/ 2
    print('median',median, 'max',maximum, 'threshold',threshold)
    return threshold



