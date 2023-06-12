import glob
import handle_phrases 
import mixer
import random
import group_mixes
import os

random.seed(9)

mixed_audio = '/Volumes/INTENSO/second_recording_session/'
tone_audio = '/Users/u050158/tone_mixed_audio/'
mixed_tone_audio = '/Volumes/INTENSO/second_recording_session_tone/'
mixed_combined_audio = '/Volumes/INTENSO/second_recording_session_combined/'

def make_all_mixes(tables = None):
    if not tables: tables = handle_phrases.Tables()
    make(tables = tables, tids = ['DVA1A','DVA2C','DVA24AK'])
    make(tables = tables, tids = ['DVA1A','DVA24AK'])
    make(tables = tables, tids = ['DVA1A'])
    make(tables = tables, tids = ['DVA2C'])
    make(tables = tables, tids = ['DVA24AK'])


def make(tables = None, tids = ['DVA1A','DVA2C','DVA24AK']):
    '''create a mix of the speakers in the listed recordings in tids
    tables is an object from the handle_phrases module to load all information of
    the IFADV recordings and transcriptions
    tids is a list of table ids linked to a specific recording with two speakers
    if three recordings are listed in tids a mix will be created with six speakers
    if two recordings are liste a mix will be created with four speakers
    the speakers in the mix will not overlap
    '''
    if not tables: tables = handle_phrases.Tables()
    ta, turns = tables.select_tables(tids)
    _make(turns, overlap = False)
    _make(turns, overlap = True)


def _make(turns, overlap):
    '''helper function of make'''
    tracks = mixer.Tracks(turns, overlap = overlap)
    tracks.make()

def add_start_tone_to_audio_files(input_dir=mixed_audio,output_dir=tone_audio):
    '''helper function to prepend a start tone to the mixes.
    used for the first recording session
    later session a start and end tone is used
    also and audio identifier file was prepended to identify the concatenated recordings
    '''
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
    '''create sets of n_recordings, uses all recordings in IFADV and reuses
    recordings if the total number of recordings is not divisible by n_recordings
    '''
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
    '''a recordings set is a list of recording ids which are mixed together
    a single recording consists of 2 speakers
    to create a mix with 4 speakers two recordings are combined
    to create a mix with 6 speakers three recordings are combined
    '''
    for recording_set in recording_sets:
        print('mixing set:', recording_set)
        make(tables = tables, tids = recording_set)
        
def make_mixes(tables = None):
    '''create mixes of speakers with all IFADV recordings.
    mixes are created with 2 4 and 6 speakers
    all recordings are used to create the sets (see make_recording_id_sets).
    (SECOND SESSION)
    '''
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

def make_group_id_to_audio_id_mapping(save = False):
    '''create a file that maps the group id (the set of speakers) to an audio id file.
    created files with 2 4 & 6 speakers the group id list the speakers in order
    created audio files with three random words these recordings are prepended to
    a speaker file to easily identify which recording is played.
    (SECOND SESSION)
    '''
    d = group_mixes.group_all_files()
    audio_ids = glob.glob('../AUDIO_ID/*.wav')
    o = []
    for group_id, audio_id in zip(d.keys(), audio_ids):
        o.append([group_id, audio_id])
    if save:
        with open(mixed_tone_audio + 'mix_id_to_audio_id_mapping.txt', 'w') as fout:
            fout.write('\n'.join(['\t'.join(line) for line in o]))
    return o
        
def add_tones_and_audio_ids_to_mixes():
    '''prepend an audio identifier and start tone and append an end tone to all mixes.
    the audio identifier is a recording of three random words that are specific to
    a given mix to easily find the specific mix in the recording.
    '''
    d = group_mixes.group_all_files()
    to_audio_id_dict= dict(make_group_id_to_audio_id_mapping(False))
    for group_id, mix_filenames in d.items():
        audio_id_filename = to_audio_id_dict[group_id]
        for mix_filename in mix_filenames:
            output_filename = mix_filename.replace(mixed_audio,mixed_tone_audio)
            print(mix_filename,audio_id_filename, output_filename)
            mixer.add_audio_id_start_and_end_tone(audio_id_filename,mix_filename,
                output_filename)

def combine_n_speaker_files(n_speakers):
    '''returns a dictionary with all audio files in order for each channel
    '''
    d = group_mixes.group_n_speakers(n_speakers)
    channels = {i:[] for i in range(1,n_speakers+1)}
    for mix_filenames in d.values():
        for mix_filename in mix_filenames:
            ch = int(mix_filename.split('_ch-')[-1].split('_')[0]) 
            channels[ch].append(mix_filename.replace(mixed_audio,mixed_tone_audio))
    return channels

def make_combined_file(filenames, channel, n_speakers):
    output_filename = mixed_combined_audio + 'nch-' + str(n_speakers) 
    output_filename += '_ch-' + str(channel) + '.wav'
    cmd = 'sox ' + ' '.join(filenames) + ' ' + output_filename
    os.system(cmd)
    
def make_all_combined_files():
    for n_speakers in [2,4,6]:
        print('handling:',n_speakers)
        channels = combine_n_speaker_files(n_speakers)
        for channel_number, filenames in channels.items():
            print('saving channel:',channel_number)
            make_combined_file(filenames,channel_number,n_speakers)

        


