import glob

mix_directory = '/Volumes/Expansion/third_recording_session/'

def group_n_speakers(n_speakers = 6, directory =None):
    if directory == None: directory = mix_directory
    fn = glob.glob(directory + 'nch-'+str(n_speakers)+'*ch*_spk*.wav')
    d = {}
    for f in fn:
        name = f.split('_spk-')[-2].split('_ch-')[0]
        if name not in d.keys(): d[name] = []
        d[name].append(f)
    return d

def group_all_files(directory =None):
    d = {}
    for n_speakers in [2,4,6]:
        d.update(group_n_speakers(n_speakers))
    return d

