import glob
import handle_phrases 
import mixer
import random

random.seed(9)

mixed_audio = '/Volumes/INTENSO/second_recording_session/'
tone_audio = '/Users/u050158/tone_mixed_audio/'

def make_all_mixes(tables = None):
    if not tables: tables = handle_phrases.Tables()
    make(tables = tables, tids = ['DVA1A','DVA2C','DVA24AK'])
    make(tables = tables, tids = ['DVA1A','DVA24AK'])
    make(tables = tables, tids = ['DVA1A'])
    make(tables = tables, tids = ['DVA2C'])
    make(tables = tables, tids = ['DVA24AK'])


def make(tables = None, tids = ['DVA1A','DVA2C','DVA24AK']):
    if not tables: tables = handle_phrases.Tables()
    ta, turns = tables.select_tables(tids)
    _make(turns, overlap = False)
    _make(turns, overlap = True)


def _make(turns, overlap):
    tracks = mixer.Tracks(turns, overlap = overlap)
    tracks.make()

def add_start_tone_to_audio_files(input_dir=mixed_audio,output_dir=tone_audio):
    fn = glob.glob(input_dir + '*.wav')
    for f in fn:
        output_filename = output_dir + 'tone_' + f.split('/')[-1]
        print(f, output_filename)
        mixer.add_start_tone(f, output_filename)
    
def get_all_table_ids():
    with open('../table_ids') as fin:
        t = fin.read().split('\n')
    return t

def make_recording_id_sets(n_recordings = 3):
    table_ids = get_all_table_ids()
    ids = table_ids[:]
    output = []
    while len(ids) > n_recordings:
        recording_set = random.sample(ids,n_recordings)
        ids = [x for x in ids if x not in recording_set]
        output.append(recording_set)
    if len(ids) > 0:
        other_ids = [x for x in table_ids if x not in ids]
        n = n_recordings - len(ids)
        output.append(ids + random.sample(other_ids,n))
    return output
        
def recording_sets_to_mix(tables, recording_sets):
    for recording_set in recording_sets:
        print('mixing set:', recording_set)
        make(tables = tables, tids = recording_set)
        
def make_mixes(tables = None):
    if not tables: tables = handle_phrases.Tables()
    print('6 speakers')
    recording_sets_6spk = make_recording_id_sets(3)
    recording_sets_to_mix(tables, recording_sets_6spk)
    print('4 speakers')
    recording_sets_4spk = make_recording_id_sets(2)
    recording_sets_to_mix(tables, recording_sets_4spk)
    print('2 speakers')
    recording_sets_2spk = make_recording_id_sets(1)
    recording_sets_to_mix(tables, recording_sets_2spk)
        
        
        
        
    
    

    

