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
        self.audio_start_time = time.time()
        record_sox.record(self.audio_filename)
        self.log_filename = self.logger.filename


    def stop(self):
        record_sox.stop_recording(self.audio_filename)
        self.logger.stop()
        self.end_time = time.time()
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
        d['end_time'] = self.end_time
        d['log_interval'] = self.interval
        return d
        
