import json
import logger
import record_sox 
import time

class Controller:
    def __init__(self, name, interval = 0.2):
        self.name = name
        self.interval = interval
        self.audio_filename = name + '.wav'
        self.filename = name + '.json'
        self.start_time = None
        self.end_time = None


    def start(self):
        self.start_time = time.time()
        self.logger = logger.Logger(self.name, self.interval) 
        self.start_audio_time = time.time()
        record_sox.record(self.audio_filename)
        self.started_audio_time = time.time()
        self.log_filename = self.logger.filename
        t = self.started_audio_time - self.start_audio_time
        self.start_dif_audio_time = t


    def stop(self):
        self.end_audio_time= time.time()
        record_sox.stop_recording(self.audio_filename)
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
        
