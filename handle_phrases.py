import ifadv_clean
import os
import subprocess

phrase_dir = ifadv_clean.ifadv_dir + 'PHRASES/'

def make_all_tables():
    o = []
    for f in ifadv_clean.table_fn:
        print(f)
        o.append(Table(f))
    return o
        

class Table:
    def __init__(self,table_filename):
        self.table_filename = table_filename
        self.table = ifadv_clean.open_table(table_filename, 
            remove_empty_table_lines = True)
        self.wav_filename = table_to_wav_filename(self.table_filename)
        self.identifier = self.wav_filename.split('/')[-1].split('.')[0]
        self._set_info()


    def _set_info(self):
        self.phrases = []
        for i in range(len(self.table)):
            self.phrases.append(Phrase(self,i))
        self.nwords = sum([p.nwords for p in self.phrases])
        self.speaker_nword_dict = {}
        self.speaker_duration_dict = {}
        self.non_overlapping_phrases = []
        for phrase in self.phrases:
            if phrase.speaker_name not in self.speaker_nword_dict.keys():
                self.speaker_nword_dict[phrase.speaker_name] = 0
                self.speaker_duration_dict[phrase.speaker_name] = 0
            self.speaker_nword_dict[phrase.speaker_name] += phrase.nwords
            self.speaker_duration_dict[phrase.speaker_name] += phrase.duration
            check_overlapping_phrases(phrase,self.phrases)
            if not phrase.overlap: self.non_overlapping_phrases.append(phrase)

class Phrase:
    def __init__(self,table, phrase_index):
        self.phrase = table.table[phrase_index]
        self.table = table
        self.phrase_index = phrase_index
        self._set_info()

    def __repr__(self):
        return self.text + ' | ' + str(self.duration) + ' | ' + self.speaker_name

    def _set_info(self):
        p = self.phrase
        self.text = p[2]
        self.speaker_name = p[1]
        self.channel = int(self.speaker_name.replace('spreker',''))
        self.start_time = p[0]
        self.end_time = p[3]
        self.nwords = p[4]
        self.duration = p[5]
        self.overlapping_phrases = []
        self.wav_filename = phrase_dir + self.table.identifier + '_pi-'
        self.wav_filename += str(self.phrase_index) + '_ch-' + str(self.channel) +'.wav'
        self.extract_audio()

    def extract_audio(self):
        if os.path.isfile(self.wav_filename): return
        cmd = 'sox ' + self.table.wav_filename + ' ' + self.wav_filename + ' '
        cmd += 'remix ' + str(self.channel) + ' trim ' + str(self.start_time)
        cmd += ' ' + str(self.duration)
        os.system(cmd)


    def check_overlap(self,other):
        if type(self) != type(other): raise ValueError(other,'is not a phrase')
        if self.table != other.table: raise ValueError('not the same ifadv recording')
        return overlap(self.start_time, self.end_time, other.start_time, other.end_time)

    @property
    def times(self):
        return self.start_time, self.end_time


def table_to_wav_filename(table_filename):
    f = table_filename.split('/')[-1].split('_')[0]
    return ifadv_clean.wav_directory + f + '.wav'

def overlap(s1,e1,s2,e2):
    if s1 <= s2:
        if e1 > s2: return True
        else: return False
    if e1 > s2: 
        if s1 < e2: return True
        else: return False

def check_overlapping_phrases(phrase,phrases):
    for i, p in enumerate(phrases):
        if phrase.phrase_index == i: continue
        if phrase.check_overlap(p):
            phrase.overlapping_phrases.append(p)
    phrase.overlap = len(phrase.overlapping_phrases) > 0
        
def phrase_to_db(phrase):
    f = phrase.wav_filename
    o = subprocess.check_output('praat get_db.praat ' + f, shell=True)
    db = o.decode('utf-8').split(' ')[0]
    return db

def make_all_phrases_db_list(tables = None):
    if not tables: tables = make_all_tables()
    output = []
    for table in tables:
        for phrase in table.phrases:
            output.append(phrase.wav_filename + '\t' + phrase_to_db(phrase))
    with open('../phrases_db_list','w') as fout:
        fout.write('\n'.join(output))
    return output
            
            