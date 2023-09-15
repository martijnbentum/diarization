'''group the channels for different sections together in dictionary
'''

import glob
import locations


def group_n_speakers(n_speakers = 6, directory =None):
    '''map section id to channel wav filename
    n_speakers      the number of speakers
    directory       the directory to search for audio files
    '''
    if directory == None: directory = locations.section_directory
    fn = glob.glob(directory + 'nch-'+str(n_speakers)+'*ch*_spk*.wav')
    d = {}
    for f in fn:
        name = f.split('_spk-')[-2].split('_ch-')[0]
        if name not in d.keys(): d[name] = []
        d[name].append(f)
    return d

def group_all_files(directory =None):
    '''group all audio files'''
    d = {}
    for n_speakers in [2,4,6]:
        d.update(group_n_speakers(n_speakers))
    return d

def group_original_ifadv_channels():
    '''group audio for each channel (2) of the original ifadv audio files.'''
    fn = glob.glob(locations.original_directory + '*.wav')
    d = {}
    for f in fn:
        name = f.split('/')[-1].split('_')[0]
        if name not in d.keys(): d[name] = []
        d[name].append(f)
    for name,fn in d.items():
        d[name] = sorted(fn)
    return d


