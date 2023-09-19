'''
Each section mix of the played audio has an orthographic transcription
to link each line in the transcription to a turn with more data
such as loudness turn wav_filename etc the Transcription object is used
The transcription object contains the corresponding turn
The transcription is part of the transcriptions object
You can create a dictionary with transcription filename as key
and a transcriptions object as value.
'''

import glob
import handle_phrases
import locations
import json

def make_filename_to_transcriptions_dict(tables = None, directory = None):
    '''create a dict with all transcriptions objects, 
    indexed by the filename of the transcription file
    '''
    if not tables: 
        Tables = handle_phrases.Tables()
        tables = Tables.tables
    d = {}
    fn = get_mix_filenames(directory)
    for filename in fn:
        if not filename_to_microphone_name(filename): continue
        f = filename.replace(locations.base, '')
        d[f] = Transcriptions(filename, tables)
    return d

def get_mix_filenames(directory = None):
    '''get all filenames of all transcription text files.'''
    if not directory: 
        # directory = locations.play_transcription_tables_directory
        directory = locations.sections_tables_directory
    return glob.glob(directory + '*.txt')

def identifier_name_to_tables(identifier, tables):
    '''find the table object(s) that correspond to a given transcription file.
    '''
    if 'nch' in identifier: return _handle_mix_filename(identifier, tables)
    if 'DVA' in identifier: return _handle_orignal_filename(identifier, tables)

def _handle_mix_filename(filename,tables):
    '''helper function for filename to table for the mix transcriptions.
    '''
    speakers = filename.split('spk-')[-1].split('.')[0].split('-')
    output = []
    for table in tables:
        add_table = True
        for speaker in table.speaker_ids: 
            if speaker not in speakers: add_table = False
        if add_table:output.append(table)
    return output

def _handle_orignal_filename(filename, tables):
    '''helper function for filename to table for the original transcriptions.
    '''
    identifier = filename.split('/')[-1].split('.')[0]
    for table in tables:
        if identifier == table.identifier: return [table]

def open_transcription(filename, parent = None):
    '''Open transcription text file and create Transcription object for each
    line.
    The transcription object can be used to find the corresponding turn
    This can be achieved by creating a Transcriptions object 
    '''
    with open(filename) as fin:
        t = [line.split('\t') for line in fin.read().split('\n') if line]
    output = []
    index = 0
    for line in t[1:]:
        if line[1] == 'other': continue
        line[0] = float(line[0])
        line[3] = float(line[3])
        output.append(Transcription(line,index, parent))
        index +=1
    return output


def get_section_played_wav_filenames(identifier):
    fn = get_play_section_wav_filenames()
    output = []
    for f in fn:
        wav_name = f.split('/')[-1].split('_ch-')[0]
        if identifier == wav_name: output.append(f)
    return output

def get_section_recorded_wav_filenames(microphone_name, identifier):
    fn = glob.glob(locations.sections_output_directory + '*.wav')
    output = []
    identifier = '_' + identifier.split('_spk-')[-1] + '_'
    # print(identifier)
    for wav_filename in fn:
        if identifier in wav_filename and microphone_name in wav_filename: 
            output.append(wav_filename)
    return output
        
def filename_to_identifier(filename):
    name = filename.split('/')[-1].split('.')[0]
    mn = ['left_respeaker', 'right_respeaker', 'shure', 'minidsp', 'grensvlak']
    for microphone_name in mn:
        if microphone_name in name: name = name.replace(microphone_name+'_','')
    return name
    
def filename_to_microphone_name(filename):
    name = filename.split('/')[-1].split('.')[0]
    mn = ['left_respeaker', 'right_respeaker', 'shure', 'minidsp', 'grensvlak']
    for microphone_name in mn:
        if microphone_name in name: return microphone_name

class Transcriptions:
    '''container object to hold all Transcription objects and match 
    corresponding turns.
    '''
    def __init__(self,filename, tables):
        self.transcription_filename = filename
        self.identifier = filename_to_identifier(filename)
        self.microphone_name = filename_to_microphone_name(filename)
        fn  = get_section_played_wav_filenames(self.identifier)
        self.section_played_wav_filenames = fn
        fn = get_section_recorded_wav_filenames(self.microphone_name, self.identifier)
        self.section_wav_filenames = fn
        self._make_speaker_to_channel_dict()
        self.tables = identifier_name_to_tables(self.identifier, tables)
        # print(filename,self.identifier, len(tables))
        self.transcriptions = open_transcription(filename,self)
        self._find_turns()
        

    def __repr__(self):
        m = 'Transcriptions: ' + self.transcription_filename.split('/')[-1]
        m += ' ok: ' + str(self.ok)
        m += ' nturns: ' + str(len(self.transcriptions))
        return m

    def _make_speaker_to_channel_dict(self):
        fn = self.section_played_wav_filenames
        self.speaker_to_channel_dict = {}
        if 'DVA' in self.transcription_filename: 
            self.speaker_to_channel_dict['spreker1'] = '1'
            self.speaker_to_channel_dict['spreker2'] = '2'
            return
        for f in fn:
            speaker = f.split('_spk-')[-1].split('.')[0]
            channel = f.split('_ch-')[-1].split('_spk-')[0]
            self.speaker_to_channel_dict[speaker] = channel
        
    def _find_turns(self):
        '''match each turn to transcription object
        not all turns will necessarily match (because the were not always used)
        all transcription objects should always match with a turn
        '''
        self.all_turns = []
        self.excluded_turns = []
        # print(self.tables)
        for table in self.tables:
            self.all_turns.extend(table.turns)
        for transcription in self.transcriptions:
            transcription.find_turn(self.all_turns, self.excluded_turns)
            if transcription.ok: self.excluded_turns.append(transcription.turn)
        self.ok = len(self.excluded_turns) == len(self.transcriptions)

    def to_json(self):
        f = self.transcription_filename.split('/')[-1].replace('.txt','.json')
        f = locations.sections_json_directory + f
        o = [transcription_to_json(t) for t in self.transcriptions]
        with open(f, 'w') as fout:
            json.dump(o,fout)
        return o
        

class Transcription:
    '''object to represent a line in a transcription text file
    can be used to match the line with a turn object to link data
    '''
    def __init__(self, line, index, parent):
        self.line = line
        self.index = index
        self.parent = parent
        self.start_time = line[0]
        self.speaker_id = line[1]
        self.microphone_name = self.parent.microphone_name
        self.text = line[2]
        self.end_time = line[3]

    def __repr__(self):
        m = 'transcription: '+str(self.index) + ' ' +self.speaker_id
        m += ' ok: ' + str(self.ok)
        return m

    def equal_to_turn(self,turn):
        equal = True
        if self.speaker_id != turn.speaker.id: equal = False
        if self.text != turn.text: equal = False
        return equal

    def find_turn(self,turns, excluded_turns = []):
        self.turn = None
        self.ok = True
        for turn in turns:
            if self.equal_to_turn(turn): 
                self.turn = turn
                return turn
        self.ok = False
        print(self,'could not find turn')

    @property    
    def channel(self):

        if 'DVA' in self.parent.identifier:
            return self.turn.phrases[0].channel
        else: return int(self.parent.speaker_to_channel_dict[self.speaker_id])
        
def _remove_base_dir(filename):
    if type(filename) == list:
        o = []
        for f in filename:
            o.append( _remove_base_directory(f) )
        return o
    else:
        f = filename.replace(locations.base, '')
        return f

def _transcription_textgrid_filename(filename):
    f = filename.replace('sections_tables','sections_textgrids')
    f = f.replace('.txt','.textgrid')
    return f 

def _find_play_audio_filenames(identifier, channel):
    if 'DVA' in identifier:
        directory = locations.original_directory 
    else:
        directory = locations.section_directory
    ch = '_ch-' + str(channel)
    fn = glob.glob(directory + '*.wav')
    for f in fn:
        if identifier in f and ch in f: 
            return _remove_base_directory(f)
        
def transcription_to_json(transcription):
    t = transcription
    d = {}
    d['identifier'] = t.parent.identifier
    d['microphone_name'] = t.microphone_name
    fn = _remove_base_dir(t.parent.section_wav_filenames)
    d['section_wav_filenames'] = fn
    f = _remove_base_dir(t.parent.transcription_filename)
    d['transcription_filename'] = f
    d['textgrid_filename'] = _transcription_textgrid_filename(f)
    d['turn_wav_filename'] = _remove_base_dir(t.turn.wav_filename)
    f = _find_play_audio_filenames(t.parent.identifier,t.channel)
    d['played_section_wav_filename']= f
    d['ifadv_wav_filename'] = _remove_base_dir(t.turn.table.wav_filename)
    d['played_channel'] = t.channel
    d['start_time'] = t.start_time
    d['end_time'] = t.end_time
    d['transcription'] = t.text
    d['played_intensity'] = t.turn.intensity
    d['speaker_id'] = t.turn.speaker.id
    d['speaker_age'] = t.turn.speaker.age
    d['speaker_sex'] = t.turn.speaker.sex
    return d
    


def get_play_section_wav_filenames():
    fn = glob.glob(locations.section_directory + '*.wav')
    return fn


