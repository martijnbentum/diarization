import glob
import random
import re
import subprocess
import os

#played audio and supporting files
base ='/Volumes/INTENSO/diarization_10-08-23/third_session_play/'
section_directory = base + 'third_recording_session/' 
combined_directory = base + 'third_recording_session_combined/'
mono_directory = base + 'third_recording_session_mono/'
tone_directory = base + 'third_recording_session_tone/'
original_directory = base + 'original/'
original_tone_directory = base + 'original_tone/'
original_combined_directory= base + 'original_combined/'
audio_id_directory = '../AUDIO_ID/'
random_word_directory = '../RANDOM_WORDS/'

#recorded audio
base_rec = '/Volumes/INTENSO/diarization_10-08-23/'
grensvlak_directory = base_rec + 'grensvlak/'
minidsp_directory = base_rec + 'minidsp/'
shure_directory = base_rec + 'shure_mxa910/'
left_respeaker_directory = base_rec + 'politie_respeaker/'
right_respeaker_directory = base_rec + 'spraakdetector_nuc/'

# audio_info = dict([line.split('\t') for line in open('../audio_info.txt').read().split('\n') if line])

def make_audio_info_dict():
    fn = glob.glob('../audio_info/*.txt')
    audio_infos = {}
    total, total_d = 0, 0
    for f in fn:
        name = f.split('/')[-1].replace('_audio_info.txt','')
        audio_info = [l.split('\t') for l in open(f).read().split('\n') if l]
        # audio_info = [[name + '_' + l[0],l[1]] for l in audio_info]
        audio_infos[name] =  dict(audio_info) 
        n = len(audio_info)
        n_d = len(audio_infos[name])
        total_d += n_d
        total += n
        # print(f, n, total, n_d, total_d) 
    return audio_infos
    


def make_audios(audio_info_dict = None):
    if not audio_info_dict: audio_info_dict = make_audio_info_dict()
    audios = {}
    for name, value in audio_info_dict.items():
        # print(k,audio_info[k])
        if name not in audios.keys(): audios[name] = {}
        for identifier,info in value.items():
            audios[name][identifier] = Audio(identifier,info)
        if not audios[name][identifier].ok: print(name, identifier)
    return audios


class Audio:
    def __init__(self,file_id, info):
        self.file_id = file_id
        self.info = info
        self._set_info()

    def __repr__(self):
        m = 'Audio: ' + self.file_id + ' | ' 
        m += self.duration + ' | ' + str(self.channels) 
        m += ' | ' + self.comp + ' | ' + self.region
        return m
            

    def _set_info(self):
        self.ok =True
        if 'Duration' not in self.info: self.ok = False
        if self.ok:
            t = self.info.split(',')
            self.path = t[0].split(':')[1]
            self.channels= int(t[1].split(':')[1])
            self.sample_rate= int(t[2].split(':')[1])
            self.precision= t[3].split(':')[1]
            self.duration= t[4].strip('Duration:').split('=')[0]
            temp = t[4].strip('Duration:').split('=')[1]
            self.samples = int(temp.split('samples')[0])
            # self.samples= int(t[4].strip('Duration:').split('=')[1].split('samples')[0])
            self.file_size= t[5].split(':')[1]
            self.bit_rate = t[6].split(':')[1]
            self.sample_encoding = t[7].split(':')[1]
            self.seconds = self.samples / self.sample_rate
            self.comp = self.path.split('/')[-3]
            self.region= self.path.split('/')[-2]


def make_time(seconds):
    seconds = int(seconds)
    h = str(seconds //3600)
    seconds = seconds % 3600
    m = str(seconds // 60)
    s = str(seconds % 60)
    if len(h) == 1:h =  '0' + h
    if len(m) == 1:m =  '0' + m
    if len(s) == 1:s = '0' + s
    return ':'.join([h,m,s])



def _make_audio_infos():
    _make_audio_info('section_audio_info.txt', section_directory)
    _make_audio_info('combined_audio_info.txt', combined_directory)
    _make_audio_info('tone_audio_info.txt', tone_directory)
    _make_audio_info('mono_audio_info.txt', mono_directory)
    _make_audio_info('minidsp_audio_info.txt', minidsp_directory)
    _make_audio_info('shure_audio_info.txt', shure_directory)
    _make_audio_info('left_respeaker_audio_info.txt', 
        left_respeaker_directory)
    _make_audio_info('right_respeaker_audio_info.txt', 
        right_respeaker_directory)
    _make_audio_info('original_audio_info.txt', original_directory)
    _make_audio_info('original_tone_audio_info.txt', original_tone_directory)
    _make_audio_info('original_combined_audio_info.txt', 
        original_combined_directory)
    _make_audio_info('audio_id_audio_info.txt', audio_id_directory)
    _make_audio_info('random_word_audio_info.txt', random_word_directory)
    _make_audio_info('grensvlak_audio_info.txt', grensvlak_directory,'.w64')
        

def _make_audio_info(output_name, audio_dir= section_directory, ext = '.wav'):
    fn = glob.glob(audio_dir + '*' + ext)
    output = []
    for f in fn:
        file_id = f.split('/')[-1].split('.')[0]
        o = subprocess.check_output('sox --i ' + f, shell =True)
        o = o.decode().replace('\n','\t').strip()
        o = o.replace('\t',',').replace("'",'')
        o = re.sub('\s+','',o)
        output.append(file_id + '\t' + o)
    with open('../audio_info/'+output_name,'w') as fout:
        fout.write('\n'.join(output))
    return output
