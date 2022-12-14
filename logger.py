import datetime
import multiprocessing
from matplotlib import pyplot as plt
import os
import record_sox
import scheduler
import time
from tuning import Tuning
import usb.core
import usb.util


class Report:
    ''' logs direction of sound angle and voice activity detection
    scheduler can be cpu intensive 
    does not reliably go faster than 1 hz
    '''
    def __init__(self,name, interval= 1):
        print('starting',time.time())
        self.devs = usb.core.find(find_all=True, idVendor=0x2886, 
            idProduct=0x0018)
        self.name = name
        self.filename = name + '.log'
        init_file(self.filename)
        self.interval = interval
        self.tunings = [Tuning(dev) for dev in self.devs]
        self.every = scheduler.every(interval, function = _report,
            maximum_nexecuters = 1,args = (self.tunings,self.filename,))
        self.running = True
             
    def stop(self):
        try: [tuning.close() for tuning in self.tunings]
        except AttributeError: print('could not close tuning connection')
        self.every.stop()
        self.running = False
            

def log_report(line, filename):
    with open(filename,'a') as fout:
        fout.write('\t'.join(map(str,line)) + '\n')

def init_file(filename):
    if not os.path.isfile(filename): return 
    if filename.endswith('.log'):
        os.system('rm ' + filename)
    with open(filename,'w') as fout:
        pass
        
def _report(tunings, filename = None):
    line = []
    for tuning in tunings:
        line.extend([ tuning.direction, tuning.is_voice(),time.time() ] )
    if filename: log_report(line, filename)
    else: print(line)


class Logger:
    ''' logs direction of sound angle and voice activity detection
    does not use scheduler less cpu load can go faster than 1 hz
    '''
    def __init__(self, name = None, interval = 0.2):
        self.devs = usb.core.find(find_all=True, idVendor=0x2886, 
            idProduct=0x0018)
        self.name = name
        if not name: self.filename = None
        else: 
            self.filename = name + '.log'
            init_file(self.filename)
        self.interval = interval
        self.tunings = [Tuning(dev) for dev in self.devs]
        self.every = scheduler.every(interval = 0,function = _logging,
            maximum_nexecuters = 1,args = (self.tunings,self.filename,interval), 
            n_times = 1)
        self.running = True

    def stop(self):
        '''stop logging data to file and close usb connection to mic array.'''
        stop_logging()
        close_connection(self.tunings)
        self.running = False

    
def _logging(tunings,filename, interval = 0.2):
    '''fast logging of direction of sound and voice activity detection.'''
    start = time.time() + interval
    while True:
        if time.time() - start > interval:
            start = time.time()
            line = []
            for tuning in tunings:
                line.extend([tuning.direction, tuning.is_voice(),time.time()])
            if filename: log_report(line, filename)
            else: print(line)
            if os.path.isfile('stop_logging'): break


def stop_logging():
    '''creates a flag to stop logging with the _logging function.
    '''
    with open('stop_logging','w') as fout:
        pass
    every = scheduler.every(interval = 2, function = _remove_stop_logging_flag, 
        maximum_nexecuters = 1, n_times = 1)

def _remove_stop_logging_flag():
    '''remove the stop logging flag.'''
    os.remove('stop_logging')


def close_connection(tunings):
    '''close the usb connection with the mic arrary after 2 seconds.'''
    every = scheduler.every(interval = 2,function = _close_usb_connection,
        maximum_nexecuters = 1,args = (tunings,), n_times = 1)

def _close_usb_connection(tunings):
    '''close the usb connection with the mic arrary.'''
    try: [tuning.close() for tuning in tunings]
    except AttributeError: print('could not close tuning connection')

def load_log(filename):
    with open(filename) as fin:
        t = fin.read().split('\n')
    output = []
    for line in t:
        if not line: continue
        oline = []
        for item in line.split('\t'):
            if '.' in item: oline.append(float(item))
            else: oline.append(int(item))
        output.append(oline)
    return output

    output = [line.split('\t') for line in t if line]
    
    return output

def load_log_start_end_time(filename):
    log = load_log(filename)
    start_time = float(log[0][2])
    end_time = float(log[-1][-1])
    return start_time, end_time


def plot_log(filename):
    log = load_log(filename)
    x = [datetime.datetime.fromtimestamp(l[-1]) for l in log]
    doa = [l[0] for l in log]
    vad = [l[1] for l in log]
    plt.ion()
    plt.clf()
    plt.plot(x,doa)
    return x, doa, vad
    
