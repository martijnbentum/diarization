import glob
import group_mixes
import handle_phrases 
import locations
import mixer
import os
import random

random.seed(9)

'''
mixed_audio = '/Volumes/Expansion/third_recording_session/'
tone_audio = '/Users/martijn.bentum/tone_mixed_audio/'
mixed_tone_audio = '/Volumes/Expansion/third_recording_session_tone/'
mixed_combined_audio = '/Volumes/Expansion/third_recording_session_combined/'
'''

def make_first_session_mixes(tables = None):
    if not tables: tables = handle_phrases.Tables()
    make(tables = tables, tids = ['DVA1A','DVA2C','DVA24AK'],make_overlap=True)
    make(tables = tables, tids = ['DVA1A','DVA24AK'], make_overlap = True)
    make(tables = tables, tids = ['DVA1A'], make_overlap=True)
    make(tables = tables, tids = ['DVA2C'], make_overlap=True)
    make(tables = tables, tids = ['DVA24AK'], make_overlap=True)


def make(tables = None, tids = ['DVA1A','DVA2C','DVA24AK'], make_overlap = False):
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
    if make_overlap:
        _make(turns, overlap = True)


def _make(turns, overlap):
    '''helper function of make'''
    tracks = mixer.Tracks(turns, overlap = overlap)
    tracks.make()

def add_start_tone_to_audio_files(input_dir=None,output_dir=None):
    '''helper function to prepend a start tone to the mixes.
    used for the first recording session
    later session a start and end tone is used
    also and audio identifier file was prepended to identify the 
    concatenated recordings
    '''
    if not input_dir:
        input_dir = locations.section_directory
    if not output_dir:
        output_dir = locations.tone_directory
    fn = glob.glob(input_dir + '*.wav')
    for f in fn:
        output_filename = output_dir + 'tone_' + f.split('/')[-1]
        print(f, output_filename)
        mixer.add_start_tone(f, output_filename)
    
def get_all_table_ids():
    with open('../table_ids') as fin:
        t = fin.read().split('\n')
    return t

# second session

def make_second_session_mixes(tables = None):
    print('make mixes')
    make_mixes_second_session(tables)
    print('add audio ids and start and end tones')
    make_group_id_to_audio_id_mapping(save = True)
    add_tones_and_audio_ids_to_mixes()
    print('combine to n speaker specific tracks')
    make_all_combined_files()


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
    if n_recordings ==1: output.pop(output.index(['DVA17AC']))
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
        
def make_mixes_second_session(tables = None):
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

def make_group_id_to_audio_id_mapping(save = False, d = None, 
    output_filename = '', audio_ids = []):
    '''create a file that maps the group id (the set of speakers) 
    to an audio id file.
    created files with 2 4 & 6 speakers the group id list the speakers in order
    created audio files with three random words these recordings are prepended to
    a speaker file to easily identify which recording is played.
    (SECOND SESSION)
    '''
    if not d: d = group_mixes.group_all_files()
    if not audio_ids: audio_ids = glob.glob('../AUDIO_ID/*.wav')
    o = []
    for group_id, audio_id in zip(d.keys(), audio_ids):
        o.append([group_id, audio_id])
    if save:
        if not output_filename:
            directory = locations.combined_directory
            t = directory + 'mix_id_to_audio_id_mapping.txt'
            output_filename = t
        print('saving to ',output_filename)
        with open(output_filename, 'w') as fout:
            fout.write('\n'.join(['\t'.join(line) for line in o]))
    return o
        
def add_tones_and_audio_ids_to_mixes(input_dir = None, 
    output_dir= None, to_audio_id_dict = None, d = None):
    '''prepend an audio identifier and start tone and append an end tone to all 
    mixes.
    the audio identifier is a recording of three random words that are specific to
    a given mix to easily find the specific mix in the recording.
    '''
    if not input_dir:
        input_dir = section_directory
    if not output_dir:
        output_dir = tone_directory
    if not d: d = group_mixes.group_all_files()
    if not to_audio_id_dict:
        to_audio_id_dict= dict(make_group_id_to_audio_id_mapping(False))
    for group_id, mix_filenames in d.items():
        audio_id_filename = to_audio_id_dict[group_id]
        for mix_filename in mix_filenames:
            output_filename = mix_filename.replace(input_dir,output_dir)
            print(mix_filename,audio_id_filename, output_filename)
            mixer.add_audio_id_start_and_end_tone(audio_id_filename,mix_filename,
                output_filename)

def combine_n_speaker_files(n_speakers, d = None, org_dir= None,
    tone_dir= None, second_split_char = '_'):
    '''returns a dictionary with all audio files in order for each channel
    '''
    if not org_dir:
        org_dir = locations.section_directory
    if not tone_dir:
        tone_dir = locations.tone_directory
    if not d:d = group_mixes.group_n_speakers(n_speakers)
    channels = {i:[] for i in range(1,n_speakers+1)}
    for mix_filenames in d.values():
        for mix_filename in mix_filenames:
            ssc = second_split_char
            ch = int(mix_filename.split('_ch-')[-1].split(ssc)[0]) 
            channels[ch].append(mix_filename.replace(org_dir,
                tone_dir))
    return channels

def make_combined_file(filenames, channel, n_speakers, 
    output_dir = None):
    if not output_dir: 
        output_dir = locations.combined_directory
    output_filename = output_dir+ 'nch-' + str(n_speakers) 
    output_filename += '_ch-' + str(channel) + '.wav'
    print('saving to ',output_filename)
    cmd = 'sox ' + ' '.join(filenames) + ' ' + output_filename
    os.system(cmd)
    
def make_all_combined_files():
    for n_speakers in [2,4,6]:
        print('handling:',n_speakers)
        channels = combine_n_speaker_files(n_speakers)
        for channel_number, filenames in channels.items():
            print('saving channel:',channel_number)
            make_combined_file(filenames,channel_number,n_speakers)

# third session
def make_third_session_mixes(tables = None):
    print('make mixes')
    if not tables: tables = handle_phrases.Tables()
    recording_sets= recording_sets_grouped_on_intensity(tables.tables)
    recording_sets_to_mix(tables, recording_sets)
    print('add audio ids and start and end tones')
    make_group_id_to_audio_id_mapping(save = True)
    add_tones_and_audio_ids_to_mixes()
    print('combine to n speaker specific tracks')
    make_all_combined_files()

def make_n_recording_id_sets_grouped_on_intensity(n_recordings = 3, 
    tables = None):
    '''create sets of n_recordings, uses all recordings in IFADV and reuses
    recordings if the total number of recordings is not divisible 
    by n_recordings
    This function groups recordings with similar intensity
    '''
    if not tables: tables = handle_phrases.make_all_tables()
    o= flat_list_to_list_of_lists(tables,3)
    output = []
    for line in o:
        output.append([x.identifier for x in line])
    return output

def recording_sets_grouped_on_intensity(tables = None):
    if not tables: tables = handle_phrases.make_all_tables()
    output = make_n_recording_id_sets_grouped_on_intensity(3, tables)
    oo = flat_list_to_list_of_lists(output,2)
    for l1, l2 in oo:
        for rec_id1,rec_id2 in zip(l1,l2):
            if rec_id1 != rec_id2:
                output.append([rec_id1,rec_id2])
    ids = [[table.identifier] for table in tables]
    output.extend(ids)
    return output

def flat_list_to_list_of_lists(flat_list,items_per_sub_list=3, reuse = True):
    output, sub_list_items= [], []
    for item in flat_list:
        if len(sub_list_items) == items_per_sub_list:
            output.append(sub_list_items)
            sub_list_items = [item]
        else: sub_list_items.append(item)
    if len(sub_list_items) < items_per_sub_list and reuse:
        for item in flat_list[::-1]:
            if len(sub_list_items) == items_per_sub_list:
                output.append(sub_list_items)
                break
            if item not in sub_list_items: 
                sub_list_items.append(item)
    return output

def extract_original_ifadv_channels():
    fn = glob.glob('../../IFADV/WAV/*.wav')
    for f in fn:
        of = f.replace('WAV/','CHANNELS/').replace('.wav','')
        of1 = of + '_ch-1.wav'
        of2 = of + '_ch-2.wav'
        os.system( 'sox ' + f + ' ' + of1 + ' remix 1' )
        os.system( 'sox ' + f + ' ' + of2 + ' remix 2' )
        print(f,of)
    return fn

def add_tones_and_audio_id_to_ifadv_channels():
    d = group_mixes.group_original_ifadv_channels()
    o = make_group_id_to_audio_id_mapping(False, 
        d, 'audio_id_mapping_orginal_ifadv.txt')
    to_audio_id_dict = dict(o)
    add_tones_and_audio_ids_to_mixes(input_dir = '../../IFADV/CHANNELS/', 
        output_dir= '../../IFADV/CHANNELS_TONE/', 
        to_audio_id_dict = to_audio_id_dict, d = d)

def combine_ifadv_channels():
    output_dir= '../../IFADV/CHANNELS_COMBINED/'
    d = group_mixes.group_original_ifadv_channels()
    channels = combine_n_speaker_files(2, d = d, 
        org_dir= '../../IFADV/CHANNELS/',
        tone_dir= '../../IFADV/CHANNELS_TONE/',
        second_split_char = '.')
    for channel_number, filenames in channels.items():
        print('saving channel:',channel_number)
        make_combined_file(filenames,channel_number,2, output_dir)

    

