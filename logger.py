import multiprocessing
import os
import record_sox
import scheduler
import time
from tuning import Tuning
import usb.core
import usb.util

dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)

class Report:
    ''' logs direction of sound angle and voice activity detection
    cannot go faster than 1 hz, due to scheduler limitation
    '''
    def __init__(self,name, interval= 1):
        print('starting',time.time())
        self.name = name
        self.filename = name + '.log'
        init_file(self.filename)
        self.interval = interval
        self.tuning = Tuning(dev)
        self.every = scheduler.every(interval, function = _report,
            maximum_nexecuters = 1,args = (self.tuning,self.filename,))
        self.running = True
             
    def stop(self):
        try: self.tuning.close()
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
        
def _report(tuning, filename = None):
    line = tuning.direction, tuning.is_voice(), time.time()
    if filename: log_report(line, filename)
    else: print(line)


class Logger:
    ''' logs direction of sound angle and voice activity detection
    can go faster than 1 hz, due to scheduler limitation
    '''
    def __init__(self, name, interval = 0.2):


def _logging(tuning,filename, interval = 0.2):
    start = time.time()
    while True:
        if time.time() - start > interval:
            start = time.time()
            line = tuning.direction, tuning.is_voice(), time.time()
            if filename: log_report(line, filename)
            else: print(line)

def start_logging(tuning,filename):
    print('record to file:',filename)
    p = multiprocessing.Process(
        target = _logging,
        args=(tuning,filename,),
        )
    p.start()
    return p


class controller:
    def __init__(self, name, interval = .1):
        self.name = name
        self.interval = interval
