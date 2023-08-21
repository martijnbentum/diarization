import os
from wonderwords import RandomWord
r = RandomWord()

audio_id_filename ='../mix_id_to_audio_id_mapping.txt'
audio_id_original_filename='../audio_id_mapping_orginal_ifadv.txt'
section_directory='/Volumes/INTENSO/diarization_10-08-23/third_session_play/'


def random_word():
    word = r.word(include_parts_of_speech=['noun','adjectives'],
        word_max_length=8)
    return word

def random_words(n):
    words = [random_word() for _ in range(n)]
    return words

def say_random_word():
    word = random_word()
    say(word)

def say_random_words(n):
    words = ' '.join(random_words(n))
    say(words)

def say(text):
    cmd = 'say -v Moira ' + text
    print(cmd)
    os.system(cmd)

def record_random_word(say_word = True):
    word = random_word()
    output_filename = word
    record(word, output_filename)
    if say_word: say(word)

def record_random_words(n, output_dir = '../RANDOM_WORDS/', say_words = False):
    words = '_'.join(random_words(n))
    output_filename = output_dir + words
    record(words, output_filename)
    if say_words: say(words)
    return words, output_filename

def record(text, output_filename):
    f = output_filename.replace('../','')
    if '.' in f:
        raise ValueError(output_filename,'should not contain extension')
    cmd = 'say -v Moira ' + text + ' -o ' + output_filename + '.aiff'
    os.system(cmd)
    print(cmd)
    sox_cmd = 'sox ' + output_filename + '.aiff -r 48000 ' + output_filename + '.wav'
    os.system(sox_cmd)
    os.system('rm ' + output_filename + '.aiff')

    



def open_mix_file(filename):
    with open(filename) as fin:
        o = [line.split('\t') for line in fin.read().split('\n') if line]
    return o

class Audio_ids:
    def __init__(self, audios = None): 
        if not audios: 
            import audio
            audios = audio.make_audios()
        self.audios = audios
        self._audio_id = open_mix_file(audio_id_filename)
        self._audio_id_original = open_mix_file(audio_id_original_filename)
        self._set_info()
        self.start_tone_duration = 6
        self.end_tone_duration = 6
        
    def _set_info(self):
        self._fix_audio_id_order()
        self.audio_ids = []
        section_set_index = 0
        last_n_speakers = False
        for index,line in enumerate(self._audio_id + self._audio_id_original):
            aid = Audio_id(line, index, section_set_index, self)
            if last_n_speakers and last_n_speakers != aid.n_speakers:
                aid.section_set_index = 0
                section_set_index = 1
            else: section_set_index += 1
            last_n_speakers = aid.n_speakers
            self.audio_ids.append(aid)

    def _fix_audio_id_order(self):
        temp = []
        for n in [6,4,2]:
            for line in self._audio_id:
                n_speakers = len(line[0].split('-'))
                if n == n_speakers: temp.append(line)
        self._audio_id = temp

class Audio_id:
    def __init__(self,line, recording_index, section_set_index, audio_ids):
        self.line = line
        self.recording_index = recording_index
        self.section_set_index = section_set_index
        self.audio_ids = audio_ids
        self._set_info()
        self._get_audios()
        self._estimate_timestamps()

    def __repr__(self):
        m = self.section_name + ' ' + str(self.n_speakers)
        m += ' ' + self.audio_id_word + ' '
        m += ' ri ' + str(self.recording_index) 
        m +=  ' si ' + str(self.section_set_index)
        m += ' ' + self.section_set_name
        m += ' start: ' + str(round(self.timestamps.start,2))
        m += ' dur: ' + str(round(self.timestamps.duration,2))
        return m

    def _set_info(self):
        self.section_name = self.line[0]
        self.filename_audio_id = self.line[1]
        self.audio_id_word = self.line[1].split('/')[-1].replace('.wav','')
        self._set_original()
        self._set_n_speakers()
        n = 'spk-' + str(self.n_speakers)
        if self.original: n += '_org'
        else: n += '_mix'
        self.section_set_name = n

    def _set_original(self):
        if '-' not in self.section_name: self.original = True
        else: self.original = False

    def _set_n_speakers(self):
        if self.original: self.n_speakers = 2
        else: self.n_speakers = len(self.section_name.split('-'))

    def _get_section_audio(self):
        if self.original: name = 'original'
        else: name = 'section'
        self.section_audio = []
        for k,audio in self.audio_ids.audios[name].items():
            if self.section_name in k: self.section_audio.append(audio)

    def _get_tone_audio(self):
        if self.original: name = 'original_tone'
        else: name = 'tone'
        self.tone_audio = []
        for k,audio in self.audio_ids.audios[name].items():
            if self.section_name in k: self.tone_audio.append(audio)

    def _get_combined_audio(self):
        if self.original: name = 'original_combined'
        else: name = 'combined'
        self.combined_audio = []
        identifier = 'nch-' + str(self.n_speakers)
        for k,audio in self.audio_ids.audios[name].items():
            if identifier in k: self.combined_audio.append(audio)

    def _get_audios(self):
        self._get_section_audio()
        self._get_tone_audio()
        self._get_combined_audio()

    def _estimate_timestamps(self):
        word = self.audio_id_word
        temp = self.audio_ids.audios['audio_id'][word]
        # word plus tones
        self.audio_id_duration = temp.seconds
        temp = self.audio_ids.audios['random_word'][word]
        #word duration only
        self.audio_id_word_duration = temp.seconds
        self.timestamps = Timestamps(self)
        if self.audio_id_duration == self.audio_id_word_duration:
            self.no_tones_audio_id = True
        else: self.no_tones_audio_id = False
        
class Timestamps:
    def __init__(self,audio_id):
        self.audio_id = audio_id
        self.recording_index = self.audio_id.recording_index
        self._set_previous()
        self._estimate_tone_section()
        self._estimate_section()

    def _set_previous(self):
        if self.recording_index == 0: self.previous_audio_id = None
        else: 
            previous_index = self.recording_index - 1
            audio_ids = self.audio_id.audio_ids.audio_ids
            self.previous_audio_id = audio_ids[previous_index]

    def _estimate_tone_section(self):
        if self.recording_index == 0: 
            self.start_tone_section = 0
        else: 
            s =  self.previous_audio_id.timestamps.end_tone_section
            self.start_tone_section = s
        self.end_tone_section = self.start_tone_section 
        self.end_tone_section = self.audio_id.tone_audio[0].seconds
        self.duration_tone = self.end_tone_section - self.start_tone_section

    def _estimate_section(self):
        self.preamble_duration = 6
        self.preamble_duration += self.audio_id.audio_id_duration
        self.start = self.start_tone_section + self.preamble_duration
        self.end = self.start + self.audio_id.section_audio[0].seconds
        self.duration = self.end - self.start
        
    def estimate_sample_index_final_start_tone(self, sample_rate):
        '''returns the estimated start index of the final start tone'''
        return int(round((self.start - 2) * sample_rate,0))

    def estimate_sample_index_first_end_tone(self, sample_rate):
        '''returns the estimated start index of the first end tone'''
        return int(round((self.end + 1) * sample_rate,0))
       
    def start_end_samples_audio_id_word(self,sample_rate):
        word_duration = self.audio_id.audio_id_word_duration 
        seconds = word_duration + 10 
        start = int(round((self.start - seconds) * sample_rate,0))
        end = int(round(start + (word_duration + 2)*sample_rate,0))
        return start, end
        

def _find_transcription_filename_section_mix(section_name):
    d = section_directory
    fn = glob.glob(d + '*'+ section_name + '*.txt')
    if fn: return fn[0]
    print('could not find section_name')
