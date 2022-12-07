import pyaudio
import wave

def open_stream(p, device_info):
    index = device_info['index']
    n_channels = device_info['maxInputChannels']
    width = pyaudio.paInt16
    stream = p.open(rate=16_000,format = width,channels = n_channels,
        input= True,input_device_index = index)
    return stream

def save_audio_frames(frames, filename = 'default.wav', n_channels = 6 ):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(n_channels)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

def record_pa(filename = 'default.wav', frames = [], seconds = 10):
    p = pyaudio.PyAudio()
    info = get_mic_array_info(p)
    stream = open_stream(p, info)
    chunk = 1024
    for i in range(0, int(16000 / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    n_channels = info['maxInputChannels']
    save_audio_frames(frames, filename, n_channels)


def get_mic_array_info(p):
    '''get audio device info.
    p       pyaudio object
    '''
    info = p.get_host_api_info_by_index(0)
    n_divices = info['deviceCount']
    for i in range(n_divices):
        info = p.get_device_info_by_host_api_device_index(0, i)
        if 'ReSpeaker 4 Mic Array' in info['name']: return info
