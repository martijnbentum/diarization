import json
import logger
import platform
import record_sox 
import scheduler
import time
import glob
import os

ifdav_dir = '/home/politie/IFADV/WAV/'

def _to_recorded_wav_name(filename):
    f = filename.split('/')[-1]
    return f.lower()

def stop_controller(controller):
    print('stopping', controller.name)
    controller.stop()

def make_controller(name, play_audio_filename, stop_time):
    print('starting', name, play_audio_filename)
    c = Controller(name, play_audio_filename)
    c.start()
    scheduler.every(
        interval = stop_time,
        function = stop_controller, 
        args = (c,),
        n_times = 1)
    
    
def record_all_ifadv(start_index = 0, skip_recorded = True):
    fn = glob.glob(ifdav_dir + '*.wav')
    start = 0
    for f in fn[start_index:]:
        output_filename = _to_recorded_wav_name(f)
        name = output_filename.split('.')[0]
        if os.path.isfile(output_filename) and skip_recorded: 
            print('skipping',f,name)
            continue
        print('setting up',f, output_filename, name)
        print('start over', start, 'seconds stops at:', start + 930)
        scheduler.every(
            interval = start,
            function = make_controller,
            args = (name, f, 930),
            n_times = 1)
        start += 933
        print('done handling',f)


class Controller:
    def __init__(self, name, play_audio_filename = None,interval = 0.2):
        self.platform = platform.platform()
        self.name = name
        self.interval = interval
        self.audio_filename = name + '.wav'
        self.filename = name + '.json'
        self.play_audio_filename = play_audio_filename
        self.start_time = None
        self.end_time = None


    def start(self):
        self.start_time = time.time()
        self.logger = logger.Logger(self.name, self.interval) 
        self.start_audio_time = time.time()
        record_sox.record(self.audio_filename, self.platform)
        self.started_audio_time = time.time()
        self.log_filename = self.logger.filename
        t = self.started_audio_time - self.start_audio_time
        self.start_dif_audio_time = t
        self.start_play_audio_time = time.time()
        if self.play_audio_filename:
            record_sox.play(self.play_audio_filename)
            self.started_play_audio_time = time.time()
            t = self.started_play_audio_time - self.start_play_audio_time
            self.start_dif_play_audio_time = t


    def stop(self):
        self.end_audio_time= time.time()
        record_sox.stop_recording()
        self.ended_audio_time= time.time()
        self.logger.stop()
        self.end_time = time.time()
        t = self.ended_audio_time - self.end_audio_time
        self.end_dif_audio_time = t
        self.save()

    def save(self):
        with open(self.filename, 'w') as fout:
            json.dump(self.dict, fout)


    @property
    def dict(self):
        d = {}
        d['name'] = self.name
        d['audio_filename'] = self.audio_filename
        d['log_filename'] = self.log_filename
        d['start_time'] = self.start_time
        d['start_audio_time'] = self.start_audio_time
        d['started_audio_time'] = self.started_audio_time
        d['start_dif_audio_time'] = self.start_dif_audio_time
        if self.play_audio_filename:
            d['start_play_audio_time'] = self.start_play_audio_time
            d['started_play_audio_time'] = self.started_play_audio_time
            d['start_dif_play_audio_time'] = self.start_dif_play_audio_time
        d['end_audio_time'] = self.end_audio_time
        d['ended_audio_time'] = self.end_audio_time
        d['end_dif_audio_time'] = self.end_dif_audio_time
        d['end_time'] = self.end_time
        d['log_interval'] = self.interval
        t = self.end_audio_time - self.start_audio_time
        d['duration_start_stop_audio_cmd'] = t
        try:audio_info = record_sox.get_sox_info(self.audio_filename)
        except: audio_info = None
        d['audio_info'] = audio_info
        try: start, end = logger.load_log_start_end_time(self.log_filename)
        except: start, end = None, None
        d['log_start_time'] = start
        d['log_end_time'] = end
        d['log_duration'] = end - start
        d['log_start_dif'] = start - self.start_time
        return d
        
