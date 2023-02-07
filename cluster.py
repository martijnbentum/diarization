import logger
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth 
import json
from collections import Counter
import numpy as np

log_dir = '../LOG/'
wav_dir = '../WAV/'

class Cluster:
    def __init__(self, name, cluster_type = '1d', nspeakers = 2): 
        self.name = name
        self.cluster_type = cluster_type
        self.nspeakers = nspeakers
        self.log_filename = log_dir + name + '.log'
        self.log = logger.load_log(self.log_filename)
        self.start_recording = self.log[0][2]
        self.json_filename = log_dir + name + '.json'
        self.json = json.load(open(self.json_filename))
        self._cluster()
        self._select_labels()
        self._make_speakers()
        self.n_speakers = len(self.speakers)
        self.n_turns = sum([len(s.turns) for s in self.speakers])

    def __repr__(self):
        m = 'cluster: ' + self.name + ' '
        m += 'n-speakers: ' + str(self.n_speakers) + ' '
        m += 'n-turns: ' + str(self.n_turns)
        return m

    def __str__(self):
        m = 'cluster: ' + self.name + '\n'
        m += 'n-speakers: ' + str(self.n_speakers) + '\n'
        m += 'n-turns: ' + str(self.n_turns) + '\n'
        for speaker in self.speakers:
            m += speaker.__repr__() + '\n'
        return m
        
        

    def _cluster(self):
        o = cluster_doa_1d(self.log_filename)
        self.doa, self.labels, self.cluster_centers, self.ms = o
        self.counts_labels = Counter(self.labels).most_common()

    def _select_labels(self):
        self.selected_labels = []
        for label, counts in self.counts_labels:
            if label >= self.nspeakers: break
            self.selected_labels.append(label)

    def _make_speakers(self):
        self.speakers = []
        for label in self.selected_labels:
            self.speakers.append(Speaker(label, self))

class Speaker:
    def __init__(self, label, cluster):
        self.label = label
        self.cluster = cluster
        self.log = cluster.log
        self.labels = cluster.labels
        self.make_turns()

    def __repr__(self):
        m = 'speaker: ' + str(self.label) + ' '
        m += 'duration: ' + str(round(self.duration,2)) + ' '
        m += 'n-turns: ' + str(len(self.turns)) + ' '
        m += 'avg-turn-dur: ' + str(round(self.avg_turn_dur,2)) + ' '
        return m

    def make_turns(self):
        indices = []
        self.turns = []
        turn_index = 0
        for i, line in enumerate(self.log):
            if self.labels[i] == self.label:
                indices.append(i)
            else:
                if indices: 
                    self.turns.append(Turn(indices, turn_index, self))
                    turn_index += 1
                indices = []
        self.duration = sum([t.duration for t in self.turns])
        self.avg_turn_dur = np.mean([t.duration for t in self.turns])


class Turn:
    def __init__(self, indices, turn_index, speaker):
        self.indices = indices
        self.n_indices= len(indices)
        self.speaker = speaker
        self.log = speaker.log
        self.label = speaker.label
        self.start_recording = speaker.cluster.start_recording
        self._set_info()

    def __repr__(self):
        m = str(self.label) + ' | '
        m += str(round(self.start_time - self.start_recording,2)) + ' - '
        m += str(round(self.end_time - self.start_recording,2)) + ' | '
        m += str(round(self.duration,2))
        return m

    def _set_info(self):
        self.start_index = self.indices[0]
        self.end_index = self.indices[-1] + 1
        if self.end_index >= len(self.log): self.end_index -= 1
        self.start_time = self.log[self.start_index][2]
        self.end_time = self.log[self.end_index][2] - 0.01
        if self.end_time <= self.start_time: 
            self.end_time = self.start_time + 0.19
            self.guessed_end_time = True
        else: self.guessed_end_time = False
        self.duration = self.end_time - self.start_time

    @property
    def log_lines(self):
        return [self.log[i] for i in self.indices]


            
        

        

def cluster_doa_1d(log_filename, quantile = 0.5, first_doa = True, 
    n_samples = None, n_jobs = None, cluster_all = True):
    '''
    cluster direction of arrival as 1d array.
    values vary from 0 - 359 (degrees) and will cluster on sound sources
    ie speakers. 
    For lower number of speakers use higher quantile and vice versa
    log_filename        the filename of the log file with doa in first or 
                        fourth column
    quantile            using 0.5 means that the median of all pairwise 
                        distances used. Use lower value if there are more 
                        speakers
    first_doa           use the first doa column, log files can contain 
                        multiple doa columns, for now assumes 1 or 2
    n_samples            influences the estimate_bandwith computation speed
                        with none all samples are used
                        for long files you might restrict the number of 
                        samples used to speed up estimation
    n_jobs              use multiple cpus to do bandwidth estimation
    cluster_all         whether to assign orphans to nearest cluster
    '''
    log = logger.load_log(log_filename)
    index = 0 if first_doa and len(log[0]) != 6 else 3
    doa = [l[index] for l in log]
    X = np.array(list(zip(doa,np.zeros(len(doa)))), dtype=int)
    bandwidth=estimate_bandwidth(X,quantile=quantile, n_samples = n_samples)
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True, n_jobs = n_jobs,
        cluster_all = cluster_all)
    ms.fit(X)
    cluster_centers = ms.cluster_centers_[:,0]
    labels = ms.labels_
    return np.array(doa), labels, cluster_centers, ms

def cluster_doa_2d(log_filename):
    log = logger.load_log(log_filename)
    index = 0 if first_doa and len(log[0]) != 6 else 3
    doa = [l[index] for l in log]
    t = [l[index+2] for l in log]
    X = np.array([doa, t])
    return X
    

    
