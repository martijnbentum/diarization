import multiprocessing
import os
import scheduler
import subprocess
import time

def record(filename, platform =None, seconds = None):
    p = start_recording(filename, platform)
    if seconds:
        stopper = scheduler.every(seconds, function = stop_recording, 
            maximum_nexecuters=1, args=(filename), n_times = 1)
    return p

def stop_recording(filename = None):
    pids = get_sox_pids(filename)
    for pid in pids:
        os.system('kill ' + pid)


def _record(filename = 'def.wav', platform = None):
    if 'macOs' in platform:
        print("starting recording at:", time.time())
        os.system('sox -d ' + filename + ' > /dev/null 2>&1')
    elif 'Linux' in platform:
        print("starting recording at:", time.time())
        os.system('sox -t alsa hw:1 ' + filename + ' > /dev/null 2>&1')
    else:
        print('unknown platform doing nothing',platform)


def start_recording(filename, platform = None):
    print('record to file:',filename)
    p = multiprocessing.Process(
        target = _record,
        args=(filename, platform),
        )
    p.start()
    return p
    
    
def get_sox_pids(filename = None):
    o = subprocess.check_output(['ps']).decode()
    pids = []
    for line in o.split('\n'):
        if 'sox' in line:
            line = line.strip()
            pid = None
            if filename and filename in line: 
                pid= line.split(' ')[0]
            elif not filename: 
                pid = line.split(' ')[0]
            if pid: pids.append(pid)
    return pids


def print_sox_pid(filename = None):
    print(get_sox_pids(filename))
    
    
def _handle_duration(d):
    x = d['duration']
    d['samples'] = int(x.split(' ')[2])
    s = x.split(' ')[0].split(':')
    s = int(s[0]) * 3600 + int(s[1]) * 60 + float(s[2])
    d['duration_seconds'] = s
    return d


def get_sox_info(filename):
    t = subprocess.check_output(['sox','--i',filename]).decode().split('\n')
    names = 'Input File,Channels,Sample Rate,Duration,File Size'.split(',')
    d = {}
    for line in t:
        if not line:continue
        for name in names:
            if name in line:
                d[name.lower().replace(' ','_')]=line.split(' : ')[-1].strip()
    d = _handle_duration(d)
    return d
                
def stop_playing(filename = None):
    pids = get_sox_pids(filename)
    for pid in pids:
        os.system('kill ' + pid)


def _play(filename):
    print("starting playing at:", time.time())
    command = 'aplay -D hw:CARD=PCH,DEV=0 '
    command += filename
    command += ' > /dev/null 2>&1'
    os.system(command)


def start_playing(filename):
    print('play file:',filename)
    p = multiprocessing.Process(
        target = _play,
        args=(filename,),
        )
    p.start()
    return p
    
        
def play(filename):
    p = start_playing(filename)
    return p


