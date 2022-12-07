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

def log_report(line, filename):
    with open(filename,'a') as fout:
        fout.write('\t'.join(map(str,line)) + '\n')

def report(tuning, interval = 1, filename = None):
    start = time.time()
    while True:
        if time.time() - start > interval:
            start = time.time()
            line = tuning.direction, tuning.is_voice(), time.time()
            if filename: log_report(line, filename)
            else: print(line)

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

def get_sox_pids(filename = None):
    o = subprocess.check_output(['ps']).decode()
    pids = []
    for line in o.split('\n'):
        if 'sox' in line:
            pid = None
            if filename and filename in line: 
                pid= line.split(' ')[0]
            elif not filename: 
                pid = line.split(' ')[0]
            if pid: pids.append(pid)
    return pids

def print_sox_pid(filename = None):
    print(get_sox_pid(filename))

def start_sox_recording(filename):
    print('record to file:',filename)
    p = multiprocessing.Process(
        target = _record_sox,
        args=(filename,),
        )
    p.start()
    return p

def stop_sox_recording(filename = None):
    pids = get_sox_pids(filename)
    for pid in pids:
        os.system('kill ' + pid)

    
def record_sox(filename, seconds = None):
    p = start_sox_recording(filename)
    if seconds:
        stopper = scheduler.every(seconds, maximum_nexecuters=1, args=(filename,),
            n_times = 1)
    return p
    
    
    

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
        


