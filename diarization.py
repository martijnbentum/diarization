import ifadv_clean
from pyannote.core import Segment, Annotation


def table_to_annotation(table_filename, max_delta_for_clustering = 0.5):
    table = ifadv_clean.open_table(table_filename, 
        remove_empty_table_lines = True)
    reference = Annotation()
    for cluster in cluster_speaker(table, 'spreker1'):
        s,e = _cluster_to_start_end_time(cluster)
        reference[Segment(s,e)] = 'A'
    for cluster in cluster_speaker(table, 'spreker2'):
        s,e = _cluster_to_start_end_time(cluster)
        reference[Segment(s,e)] = 'B'
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
        


    
        
   


