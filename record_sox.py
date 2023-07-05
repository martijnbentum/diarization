import multiprocessing
import glob
import os
import scheduler
import subprocess
import time


def record(filename, platform =None, seconds = None):
    o = filename.split('.')
    if len(o) == 1 or o[-1] not in ['wav','flac','raw']: 
        raise ValueError(filename, 'does not endwith .wav or .flac or .raw')
    p = start_recording(filename, platform)
    if seconds:
        stopper = scheduler.every(seconds, function = stop_recording, 
            maximum_nexecuters=1, n_times = 1)
    return p

def stop_recording(filename = None):
    print('stop recording:',filename)
    pids = get_sox_pids(filename)
    for pid in pids:
        os.system('kill ' + pid)


def _record(filename = 'def.wav', platform = None):
    if 'macOS' in platform:
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
    try:
        x = d['duration']
        d['samples'] = int(x.split(' ')[2])
        s = x.split(' ')[0].split(':')
        s = int(s[0]) * 3600 + int(s[1]) * 60 + float(s[2])
        d['duration_seconds'] = s
    except KeyError:
        d['samples'] = None
        d['duration_seconds'] = None
    return d


def get_sox_info(filename):
    if not os.path.isfile(filename): return None
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

def move_empty_turns():
    from handle_phrases import turn_dir
    output_dir = '../BAD_TURNS/'
    fn = glob.glob(turn_dir + '*.wav') 
    for f in fn:
        d = get_sox_info(f)
        if not d or d['duration_seconds'] == None:
            print('moving ', f, f.replace(turn_dir, output_dir)) 
            os.system('cp ' + f + ' ' + f.replace(turn_dir, output_dir))

def check_turn_duration(tables):
    from handle_phrases import turn_dir
    from make_mix import get_all_table_ids
    table_ids = get_all_table_ids()
    fn = glob.glob(turn_dir + '*.wav') 
    bads = []
    for table_id in table_ids:
        print(table_id)
        ta, turns = tables.select_tables([table_id])
        for turn in turns:
            d = get_sox_info(turn.wav_filename)
            if not d: continue
            if d['duration_seconds'] != turn.duration:
                print(turn.wav_filename,d)
                bads.append([turn,d])
    return bads
        


