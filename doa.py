import multiprocessing
import os
import pyaudio
import subprocess
from tuning import Tuning
import usb.core
import usb.util
import time
import wave

'''
pyaudio example:
https://people.csail.mit.edu/hubert/pyaudio/

respeaker example:
https://wiki.seeedstudio.com/ReSpeaker_Mic_Array_v2.0/
'''
 
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
 
'''
if dev:
    Mic_tuning = Tuning(dev)
    print(Mic_tuning.direction )
    while True:
        print( Mic_tuning.direction ,time.time())
        time.sleep(1)
'''


def get_tuning():
    return Tuning(dev)

def report(tuning, interval = 1):
    start = time.time()
    while True:
        if time.time() - start > interval:
            start = time.time()
            print(tuning.direction, tuning.is_voice(), time.time())

def get_mic_array_info(p):
    info = p.get_host_api_info_by_index(0)
    n_divices = info['deviceCount']
    for i in range(n_divices):
        info = p.get_device_info_by_host_api_device_index(0, i)
        if 'ReSpeaker 4 Mic Array' in info['name']: return info

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


def _record_sox(filename = 'def.wav'):
    print("starting recording at:", time.time())
    os.system('sox -d ' + filename + ' > /dev/null 2>&1')

def _find_sox_pid(filename = None):
    o = subprocess.check_output(['ps']).decode()
    for line in o.split('\n'):
        if 'sox' in line:
            if filename and filename: return line.split(' ')[0]
            if not filename: return line.split(' ')[0]
    return False

def print_sox_pid(filename = None):
    print(_find_sox_pid(filename))

def record_sox(filename = 'def.wav'):
    p1 = multiprocessing.Process(
        target = _record_sox,
        args=(filename,),
        )
    p1.start()
    sox_pid = find_sox_pid(filename)
    return p1, sox_pid

    
    
    

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
        


