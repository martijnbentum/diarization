import audio_identifier
import glob
import json
import locations
import numpy as np
import os
import scipy.io.wavfile as wav
import soundfile as sf
import scipy.signal as signal


class Recordings:
    def __init__(self, find_start = False, sections_output_directory = None):
        if not sections_output_directory:
            directory = locations.sections_output_directory
            self.sections_output_directory = directory
        self.find_start = find_start
        self.audio_ids = audio_identifier.Audio_ids()
        self.audios = self.audio_ids.audios
        self._set_channel_infos()
        self.microphone_names = 'left_respeaker,right_respeaker,shure'
        self.microphone_names += ',minidsp,grensvlak'
        self.microphone_names = self.microphone_names.split(',')
        self._make_recordings()
        self.sections_made = False

    def _set_channel_infos(self):
        filename = locations.recording_name_channels_filename
        t = open(filename).read().split('\n')
        d = dict([line.split('|') for line in t if line])
        self.channel_infos = {}
        for microphone_name, info in d.items():
            channels, selected, combined, processed = info.split(' ')
            channels = list(map(int,channels.split(',')))
            selected = int(selected)
            if combined == 'None': combined = None
            else: combined = int(combined)
            if processed == 'None': processed = None
            else: processed = int(processed)
            self.channel_infos[microphone_name] = {'channels':channels,
                'selected':selected,'combined':combined, 
                'processed':processed}

    def _make_recordings(self):
        self.recordings = []
        for microphone_name in self.microphone_names:
            recording = Recording(microphone_name, self)
            self.recordings.append(recording)

    def make_all_sections(self):
        for recording in self.recordings:
            print(recording.microphone_name,'making sections')
            recording.make_sections()
        self.sections_made = True

    def extract_audio_sections_for_all_recordings(self):
        directory = self.sections_output_directory
        for recording in self.recordings:
            print(recording.microphone_name)
            if not self.sections_made:
                print('making sections')
                recording.make_sections()
            print('extracting audio')
            recording.extract_audio_all_sections(directory)


class Recording:
    def __init__(self, microphone_name, recordings):
        self.microphone_name = microphone_name
        self.recordings = recordings
        d = self.recordings.channel_infos[self.microphone_name]
        self.audios = self.recordings.audios[self.microphone_name]
        self.channel_info = d
        self._make_channel_to_audio_dict()
        self._find_audio_info()
        if self.recordings.find_start: self._find_start()

    def __repr__(self):
        m = 'recording ' + self.microphone_name + ' '
        m += str(self.selected_channel)
        m += str(self.n_sections) + ' '
        m += str(self.n_warnings) + ' '
        m += str(self.n_errors) 
        return m

    def _make_channel_to_audio_dict(self):
        self.channel_to_audio_dict = {}
        for name, audio in self.audios.items():
            if 'track' in name: ch = int(name.split('_')[-1])
            elif '_ch-' in name: ch = int(name.split('_ch-')[-1])
            else: continue
            self.channel_to_audio_dict[ch] = audio

    def _find_audio_info(self):
        self.selected_channel = self.channel_info['selected']
        self.selected_audio=self.channel_to_audio_dict[self.selected_channel]
        '''
        for name, audio in self.audios.items():
            if self.selected_channel in name: 
                self.selected_audio= audio
                break
        '''

    def _make_wav_filename(self):
        self.wav_filename = self.selected_audio.path
        if locations.path == locations.mac_path: return
        f = self.wav_filename
        self.wav_filename = f.replace(locations.mac_path, locations.path)

    def _find_start(self):
        self._make_wav_filename()
        self.sample_rate= self.selected_audio.sample_rate
        self.start_audio, sr = sf.read(self.wav_filename, start = 0,
            stop = 300 * self.sample_rate)
        self._handle_tones(500,self.start_audio,'first_start_tones')
        self._find_start_time()
        self.audio_ids = audio_identifier.Audio_ids(
            start_time = self.start_time_tone_section)

    def _handle_tones(self,frequency, audio, name):
        d = {'sample_rate':self.sample_rate,'input_signal':audio,
            'frequency':frequency, 'return_all': True}
        o, ts, m = get_start_end_timestamps(**d)
        tones = []
        for index,line in enumerate(o):
            start, end = line
            tones.append(Tone(index,name,start,end,self,frequency))    
        setattr(self, name, tones)
        self._magnitudes = m
        self._timestamps = ts

    def _find_start_time(self):
        audio_ids = self.recordings.audio_ids.audio_ids
        word_duration = audio_ids[0].audio_id_word_duration
        time_to_first_start_tone = word_duration + 8
        start_tone = self.first_start_tones[0].start
        self.start_time_tone_section = start_tone - time_to_first_start_tone
        
    def make_sections(self):
        self.sections = []
        self.errors = []
        self.warnings = []
        for index, audio_id in enumerate(self.audio_ids.audio_ids):
            if index == 0: start_tones = self.first_start_tones
            else: start_tones = None
            section = Section(index, audio_id,self, start_tones)
            if section.delta_warning or section.tone_warning:
                self.warnings.append(section)
            if section.ok:
                self.sections.append(section)
            else: self.errors.append(section)
        self.n_errors = len(self.errors)
        self.n_warnings = len(self.warnings)
        self.n_sections = len(self.sections)

    def extract_audio_all_sections(self, goal_directory = ''):
        for section in self.sections:
            section.extract_section_from_all_channels(goal_directory)
            section_to_json(section)
        
class Section:
    def __init__(self, index, audio_id, recording, start_tones = None, 
        delta = 2, debug = True):
        self.index = index
        self.audio_id = audio_id
        self.section_name = self.audio_id.section_name
        self.recording = recording
        self.sample_rate = self.recording.sample_rate
        self.start_tones = start_tones
        self.debug = debug
        self.delta = delta
        self.ok = True
        if not self.start_tones: self._find_start_tones()
        else: self._start_time_start_audio = 0
        self._set_start_end_section()
        self._find_end_tones()
        self._set_accuracy()

    def __repr__(self):
        m = 'Section: ' + str(self.index) + ' '
        m += self.section_name + ' '
        m += self.recording.microphone_name + ' '
        m += str(round(self.start,2)) + ' '
        m += str(round(self.end,2)) + ' '
        m += str(round(self.duration,2)) + ' '
        m += str(round(self.start_delta,2)) + ' '
        m += str(round(self.end_delta,2)) + ' ' 
        m += str(self.n_start_tones) + ' ' + str(self.n_end_tones)
        return m

    def _make_index(self,seconds):
        return int(round(seconds * self.sample_rate,0))

    def _get_start_audio(self):
        start = self.audio_id.timestamps.start_tone_section - 20
        start_index = self._make_index(start)
        end = self.audio_id.timestamps.start + 20
        end_index = self._make_index(end)
        self.start_audio, sr = sf.read(
            self.recording.wav_filename, 
            start = start_index,
            stop = end_index)
        self._start_time_start_audio = start
        self._end_time_start_audio = end

    def _find_start_tones(self):
        frequency = 500
        self._get_start_audio()
        d = {'sample_rate':self.recording.sample_rate,
            'input_signal':self.start_audio,
            'frequency':frequency, 'return_all': True}
        o, ts, m = get_start_end_timestamps(**d)
        self.start_tones = []
        for index,line in enumerate(o):
            start, end = line
            tone = Tone(index,'start',start,end,self,frequency)    
            self.start_tones.append(tone)
        if self.debug:
            self._start_magnitudes = m

    def _set_start_end_section(self):
        print(self.section_name,self.index,self.start_tones)
        self.n_start_tones = len(self.start_tones)
        if self.n_start_tones == 0: 
            self.ok = False
            return
        self.start = self.start_tones[-1].end + 1 + self._start_time_start_audio
        self.end = self.start + self.audio_id.section_audio[0].seconds
        self.duration = self.end - self.start

    def _get_end_audio(self):
        start = self.end - 20
        start_index = self._make_index(start)
        end = self.end + 20
        end_index = self._make_index(end)
        self.end_audio, sr = sf.read(
            self.recording.wav_filename, 
            start = start_index,
            stop = end_index)
        self._start_time_end_audio = start
        self._end_time_end_audio = end

    def _find_end_tones(self):
        frequency = 300
        self._get_end_audio()
        d = {'sample_rate':self.recording.sample_rate,
            'input_signal':self.end_audio,
            'frequency':frequency, 'return_all': True}
        o, ts, m = get_start_end_timestamps(**d)
        self.end_tones = []
        for index,line in enumerate(o):
            start, end = line
            tone = Tone(index,'end',start,end,self,frequency)    
            self.end_tones.append(tone)
        if self.debug:
            self._end_magnitudes = m
        self.n_end_tones = len(self.end_tones)
        if self.n_end_tones == 0: self.end_tone_estimated_end = 0
        else:
            self.end_tone_estimated_end = self._start_time_end_audio 
            self.end_tone_estimated_end += self.end_tones[0].start - 1

    def _set_accuracy(self):
        self.start_delta = self.audio_id.timestamps.start - self.start
        self.end_delta = self.end_tone_estimated_end - self.end
        self.delta_warning, self.tone_warning = False, False
        if abs(self.end_delta) > 1: self.delta_warning = True
        if self.n_start_tones < 2:self.tone_warning = True

    def _make_wav_filename_base(self, goal_directory= ''):
        if not os.path.isdir(goal_directory): 
            print(goal_directory, 'does not exists saving to currect directory')
            goal_directory = ''
        m = goal_directory
        m += self.recording.microphone_name + '_' + str(self.index) + '_'
        m += self.section_name
        self.wav_filename_base = m

    def extract_section_from_all_channels(self, goal_directory = ''):
        for channel in self.recording.channel_to_audio_dict.keys():
            self.extract_audio(channel, goal_directory)

    def extract_audio(self, channel, goal_directory = ''):
        self._make_wav_filename_base(goal_directory)
        audio_info = self.recording.channel_to_audio_dict[channel]
        input_filename = audio_info.path
        wav_filename = self.wav_filename_base + '_ch-' + str(channel) + '.wav'
        if os.path.isfile(wav_filename): return
        cmd = 'sox ' + input_filename + ' ' + wav_filename + ' '
        cmd += ' trim ' + str(self.start - self.delta)
        cmd += ' ' + str(self.duration + self.delta)
        print(cmd)
        os.system(cmd)
        

class Tone:
    def __init__(self, index, name,start, end, parent, frequency):
        self.index = index
        self.name = name
        self.start = start
        self.end = end
        self.duration = self.end - self.start
        self.parent =parent 
        self.frequency = frequency
        self.sample_rate = self.parent.sample_rate
        self.start_sample_index = int(self.start * self.sample_rate)
        self.end_sample_index = int(self.end * self.sample_rate)

    def __repr__(self):
        m = self.name + ' ' + str(self.index) + ' '
        m += str(self.start) + ' - ' + str(self.end) + ' | '
        m += str(self.duration)
        return m
    
        
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


def section_to_json(section, return_dict = False):
    path = locations.json_sections_output_directory
    filename = path + section.wav_filename_base.split('/')[-1] + '.json'
    keys = 'index,section_name,sample_rate,ok,n_start_tones,start,end'
    keys += ',duration,n_end_tones,end_tone_estimated_end,start_delta'
    keys += ',end_delta,delta'
    keys = keys.split(',')
    d = {}
    for key in keys:
        d[key] = section.__dict__[key]
    d['microphone_name'] = section.recording.microphone_name
    with open(filename, 'w') as fout:
        json.dump(d,fout)
    if return_dict:
        return d
    
    


