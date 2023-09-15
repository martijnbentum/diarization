'''Diarization based on degree of arrival as provided by respeaker.'''

import ifadv_clean
from pyannote.core import Segment, Annotation, notebook
from pyannote.metrics.diarization import DiarizationErrorRate
import cluster
import glob
import ifadv_clean
from matplotlib import pyplot as plt
import pickle


def make_all_diarizations(filename = '../diariazations.pickle', save = False):
    '''make all diarization objects for available log + ifadv tables.'''
    fn = glob.glob('../LOG/*.log')
    o=[]
    for f in fn:
        print(f)
        name = f.split('/')[-1].split('.')[0]
        if not name_to_ifadv_table(name):
            print('cannot find ifadv table')
            continue
        o.append( Diarization(f) )
    with open(filename,'wb') as fout:
        pickle.dump(o, fout)
    return o

def load_diarizations(filename = '../diariazations.pickle'):
    with open(filename,'rb') as fin:
        o = pickle.load(fin)
    return o
    

class Diarization:
    '''contains clustering based on mic array and ifadv transcriptions.'''
    def __init__(self,name):
        self.cluster = cluster.Cluster(name)
        self.hypothesis = cluster_to_annotation(name)
        self.name = self.cluster.name
        self.ifadv_table_filename = name_to_ifadv_table(self.name)
        self.reference = table_to_annotation(self.ifadv_table_filename)
        self.metric = DiarizationErrorRate()
        self.der_output = self.metric(self.reference,self.hypothesis,
            detailed = True)
        d = self.metric.mapper_(self.reference,self.hypothesis)
        self.label_map = d
        self.der = self.der_output['diarization error rate']

    def __repr__(self):
        m = self.name.ljust(30) + str(round(self.der,3))
        return m

    def __str__(self):
        m = self.__repr__() + '\n'
        for k,v in self.der_output.items():
            m += k.ljust(30) + str(round(v,3)) + '\n'
        m += str(self.label_map)
        return m

    def plot(self,start = 0, end = 40):
        ref = table_to_annotation(self.ifadv_table_filename,
            label_map =self.label_map)
        plot_ref_hyp(ref,self.hypothesis,start,end)

def name_to_ifadv_table(name):
    for f in ifadv_clean.table_fn:
        temp = f.lower()
        if name in temp: return f

def plot_ref_hyp(ref, hyp, start = 0, end = 40 ):
    plt.ion()
    plt.clf()
    notebook.width = 10
    notebook.crop = Segment(start, end)
    plt.subplot(211)
    notebook.plot_annotation(ref, legend =True, time = False)
    plt.gca().text(0.6, 0.15, 'reference', fontsize = 16)
    plt.subplot(212)
    notebook.plot_annotation(hyp, legend =True, time = False)
    plt.gca().text(0.6, 0.15, 'hypothesis', fontsize = 16)
    

def compute_reference_hypothesis(name):
    c = cluster.Cluster(name)
    hypothesis = cluster_to_annotation(name)
    name = c.name
    f = name_to_ifadv_table(name)
    reference = table_to_annotation(f)
    return reference, hypothesis

def cluster_to_annotation(log_filename):
    c = cluster.Cluster(log_filename)
    hypothesis = Annotation()
    for turn in c.speakers[0].turns:
        s, e = turn.start_time, turn.end_time
        hypothesis[Segment(s,e),1] = 'a'
    for turn in c.speakers[1].turns:
        s, e = turn.start_time, turn.end_time
        hypothesis[Segment(s,e),2] = 'b'
    return hypothesis

def table_to_annotation(table_filename, max_delta_for_clustering = 0.5,
    label_map = None):
    spreker1, spreker2 = 'spreker1','spreker2'
    if label_map:
        spreker1 = label_map[spreker1]
        spreker2 = label_map[spreker2]
    table = ifadv_clean.open_table(table_filename, 
        remove_empty_table_lines = True)
    reference = Annotation()
    for cluster in cluster_speaker(table, 'spreker1'):
        s,e = _cluster_to_start_end_time(cluster)
        reference[Segment(s,e)] = spreker1
    for cluster in cluster_speaker(table, 'spreker2'):
        s,e = _cluster_to_start_end_time(cluster)
        reference[Segment(s,e)] = spreker2
    return reference


def _cluster_to_start_end_time(cluster):
    start_time = cluster[0][0]
    end_time = cluster[-1][3]
    return start_time, end_time
        

def cluster_speaker(table, speaker_name, max_delta_for_clustering = 0.5):
    '''combines table lines from same speaker 
    if not interupted and not futher apart than max_delta...
    '''
    output = []
    cluster = []
    for line in table:
        start, end  = line[0], line[3]
        if line[1] == speaker_name: 
            if len(cluster) > 0:
                last_end = cluster[-1][3]
                if start - last_end > max_delta_for_clustering:
                    if cluster:
                        output.append(cluster)
                        cluster = []
            cluster.append(line)
        elif cluster:
            output.append(cluster)
            cluster = []
    return output
        


    
        
   


