import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as signal

# used chatgpt for setup with the following prompts:
# i want to detect the onset of a pure tone in an audio recording with fft
# can you give a python implementation

def load_audio(filename):
    sample_rate, audio_data = wav.read(filename)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 1]
    return sample_rate, audio_data

def get_start_end_timestamps(filename, frequency = 500):
    sr, magnitudes= sliding_window_with_hamming(filename, frequency)
    threshold = _find_threshold(magnitudes)
    timestamps = _get_timestamps(sr, magnitudes)
    output = []
    index = 0
    while True:
        start, end, index = find_segment(magnitudes, index, threshold)
        if not start and not end: break
        output.append([timestamps[start], timestamps[end]])
    return output

def sliding_window_with_hamming(filename, frequency = 500, 
    window_size_ms = 500):
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
    return output_sample_rate, output_signal, 

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
            threshold, 'is: ', samples[index])
    
def _get_timestamps(sr, samples):
    increments = 1/ sr
    timestamps = [round(i *increments,4) for i in range(len(samples))]
    return timestamps

def _find_threshold(samples):
    return (np.max(samples) + np.median(samples))/ 2

