import multiprocessing
import os
import scheduler
import subprocess
import time

def record(filename, seconds = None):
    p = start_recording(filename)
    if seconds:
        stopper = scheduler.every(seconds, maximum_nexecuters=1, args=(filename,),
            n_times = 1)
    return p


def stop_recording(filename = None):
    pids = get_sox_pids(filename)
    for pid in pids:
        os.system('kill ' + pid)


def _record(filename = 'def.wav'):
    print("starting recording at:", time.time())
    os.system('sox -d ' + filename + ' > /dev/null 2>&1')

def start_recording(filename):
    print('record to file:',filename)
    p = multiprocessing.Process(
        target = _record,
        args=(filename,),
        )
    p.start()
    return p
    
    
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
    print(get_sox_pids(filename))
    
    

        


