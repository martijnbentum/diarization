'''
module to split ifadv recordings in phrases (transcription unit)
Table object holds all transcription phrases for a given recording
Phrase object points to extracted phrase wav file and links to metadata
'''

import ifadv_clean
import os
import subprocess
import play_audio
import speakers

phrase_dir = ifadv_clean.ifadv_dir + 'PHRASES/'
turn_dir = ifadv_clean.ifadv_dir + 'TURNS/'

def make_all_tables():
    o = []
    for f in ifadv_clean.table_fn:
        print(f)
        o.append(Table(f))
    return o
        

class Table:
    '''
    Transcription phrases for a single recordings
    15 minutes of dialogues (two speakers)
    links to Phrase object which links to extract wav audio file of the phrase
    '''
    def __init__(self,table_filename):
        self.table_filename = table_filename
        self.table = ifadv_clean.open_table(table_filename, 
            remove_empty_table_lines = True)
        self.wav_filename = table_to_wav_filename(self.table_filename)
        self.identifier = self.wav_filename.split('/')[-1].split('.')[0]
        self.recording = speakers.make_recording(self.wav_filename)
        self._make_phrases()
        self._make_turns()


    def _make_phrases(self):
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

    def _make_turns(self):
        self.turns = []
        turn_index = 0
        for phrase in self.phrases:
            if phrase.part_of_turn: continue
            if not phrase.phrase_wav_file_exists: continue
            self.turns.append(Turn(self, phrase, turn_index))
            turn_index +=1
        self.non_overlapping_turns = []
        for turn in self.turns:
            if not turn.overlap: self.non_overlapping_turns.append(turn)
            turn.set_overlapping_turns()


class Turn:
    def __init__(self,table,phrase, turn_index, silence_delta = 0.5):
        self.table = table
        self.start_phrase = phrase
        self.turn_index = turn_index
        self.silence_delta = silence_delta
        self._find_other_phrases()
        self._set_info()

    def __repr__(self):
        m = self.text[:80].ljust(80) + ' | s: '
        m += str(round(self.duration,2)).ljust(5) + ' | o: '
        m += str(self.overlap).ljust(5) + ' | np: '
        m += str(self.nphrases).ljust(2) + ' | s: '
        m += self.start_phrase.speaker_name
        return m

    def _find_other_phrases(self):
        self.phrases = [self.start_phrase]
        start_index = self.start_phrase.phrase_index + 1
        for phrase in self.table.phrases[start_index:]:
            if phrase.part_of_turn: break
            if phrase.speaker_name != self.start_phrase.speaker_name: break
            delta = phrase.start_time - self.phrases[-1].end_time 
            if delta > self.silence_delta: break
            self.phrases.append(phrase)
            phrase.part_of_turn = True
            self.turn = self

    def _set_info(self):
        self.start_time = self.phrases[0].start_time
        self.end_time = self.phrases[-1].end_time
        self.nphrases = len(self.phrases)
        self.nwords = sum([phrase.nwords for phrase in self.phrases])
        self.duration = self.end_time - self.start_time
        self.speaker = self.start_phrase.speaker
        self.channel= self.start_phrase.channel
        self.recording = self.table.recording
        self.end_phrase = self.phrases[-1]
        self.overlap = True if sum([p.overlap for p in self.phrases]) > 0 else False
        self.text = ' '.join([p.text for p in self.phrases])
        self.wav_filename = turn_dir + self.table.identifier 
        self.wav_filename += '_ti-' + str(self.turn_index) 
        self.wav_filename += '_ch-' + str(self.channel) + '.wav'

    def set_overlapping_turns(self):
        self.overlapping_turns = []
        if not self.overlap: return
        for phrase in self.phrases:
            for overlap_phrase in phrase.overlapping_phrases:
                if not overlap_phrase.turn: continue 
                if overlap_phrase.turn not in self.overlapping_turns:
                    self.overlapping_turns.append(overlap_phrase.turn)
                

    def extract_audio(self):
        if os.path.isfile(self.wav_filename): return
        cmd = 'sox ' + self.table.wav_filename + ' ' + self.wav_filename + ' '
        cmd += 'remix ' + str(self.channel) + ' trim ' + str(self.start_time)
        cmd += ' ' + str(self.duration)
        print(cmd)
        os.system(cmd)

    def play(self):
        print(self.text)
        print('play')
        cmd = 'sox ' + self.table.wav_filename + ' -p trim '
        cmd += str(self.start_time) + ' ' + str(self.duration)
        cmd += ' remix ' + str(self.channel)
        cmd += ' | play -'
        print(cmd)
        os.system(cmd)

        

class Phrase:
    '''
    a phrase is a transcription unit, an utterance of a single speaker
    a phrase can overlap in time with a phrase of another speaker
    the Speaker object contains meta data of the speaker of the phrase
    the phrase is linked to wav audio file with the extracte phrase
    '''
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
        self.speaker = self.table.recording.channel_to_speaker(self.channel)
        self.start_time = p[0]
        self.end_time = p[3]
        self.nwords = p[4]
        self.duration = p[5]
        self.overlapping_phrases = []
        self.wav_filename = phrase_dir + self.table.identifier + '_pi-'
        self.wav_filename += str(self.phrase_index) + '_ch-' + str(self.channel) +'.wav'
        self.extract_audio()
        self.part_of_turn = False
        self.turn = None

    def extract_audio(self):
        if os.path.isfile(self.wav_filename): return
        cmd = 'sox ' + self.table.wav_filename + ' ' + self.wav_filename + ' '
        cmd += 'remix ' + str(self.channel) + ' trim ' + str(self.start_time)
        cmd += ' ' + str(self.duration)
        print(cmd)
        os.system(cmd)

    def play(self):
        print(self.__repr__())
        play_audio.play(self.wav_filename)
        

    def check_overlap(self,other):
        if type(self) != type(other): raise ValueError(other,'is not a phrase')
        if self.table != other.table: raise ValueError('not the same ifadv recording')
        return overlap(self.start_time, self.end_time, other.start_time, other.end_time)

    @property
    def times(self):
        return self.start_time, self.end_time

    @property
    def phrase_wav_file_exists(self):
        return os.path.isfile(self.wav_filename)
        
    


def table_to_wav_filename(table_filename):
    '''maps table filename to wav filename.'''
    f = table_filename.split('/')[-1].split('_')[0]
    return ifadv_clean.wav_directory + f + '.wav'

def overlap(s1,e1,s2,e2):
    '''check whether start and end point of two phrases overlap.'''
    if s1 <= s2:
        if e1 > s2: return True
        else: return False
    if e1 > s2: 
        if s1 < e2: return True
        else: return False

def check_overlapping_phrases(phrase,phrases):
    '''checks whether a phrase overlaps with other phrases.
    overlapping phrases are stored in in the overlapping_phrases attribute
    '''
    for i, p in enumerate(phrases):
        if phrase.phrase_index == i: continue
        if phrase.check_overlap(p):
            phrase.overlapping_phrases.append(p)
    phrase.overlap = len(phrase.overlapping_phrases) > 0
        
def phrase_to_db(phrase):
    '''compute intensity for a phrase with praat.'''
    f = phrase.wav_filename
    o = subprocess.check_output('praat get_db.praat ' + f, shell=True)
    db = o.decode('utf-8').split(' ')[0]
    return db

def turn_to_db(turn):
    f = turn.wav_filename
    o = subprocess.check_output('praat get_db.praat ' + f, shell=True)
    db = o.decode('utf-8').split(' ')[0]
    return db

def make_all_phrases_db_list(tables = None):
    '''make all phrase audio files.'''
    if not tables: tables = make_all_tables()
    output = []
    for table in tables:
        print(table.table_filename)
        for phrase in table.phrases:
            if not os.path.isfile(phrase.wav_filename): continue
            try: db = phrase_to_db(phrase)
            except: continue
            output.append(phrase.wav_filename + '\t' + db)
    with open('../phrases_db_list','w') as fout:
        fout.write('\n'.join(output))
    return output
            
def make_all_turn_db_list(tables = None):
    if not tables: tables = make_all_tables()
    output = []
    for table in tables:
        print(table.table_filename)
        for turn in table.turns:
            if not os.path.isfile(turn.wav_filename): continue
            try: db = turn_to_db(turn)
            except: continue
            output.append(turn.wav_filename + '\t' + db)
    with open('../turn_db_list','w') as fout:
        fout.write('\n'.join(output))
    return output
            
