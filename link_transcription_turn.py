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
        d[filename] = Transcriptions(filename, tables)
    return d

def make_filename_tables_dict(tables = None, directory = None):
    ''' link each transcription filename to the corresponding table objects.
    not directly used to create the transcriptions objects
    '''
    if not tables: 
        Tables = handle_phrases.Tables()
        tables = Tables.tables
    fn = get_mix_filenames(directory)
    d = {}
    for filename in fn:
        d[filename] = filename_to_tables(filename, tables)
    return d

def get_mix_filenames(directory = None):
    '''get all filenames of all transcription text files.'''
    if not directory: 
        directory = locations.play_transcription_tables_directory
    return glob.glob(directory + '*.txt')

def filename_to_tables(filename, tables):
    '''find the table object(s) that correspond to a given transcription file.
    '''
    if 'nch' in filename: return _handle_mix_filename(filename, tables)
    if 'DVA' in filename: return _handle_orignal_filename(filename, tables)

def _handle_mix_filename(filename,tables):
    '''helper function for filename to table for the mix transcriptions.
    '''
    speakers = filename.split('spk-')[-1].split('.')[0].split('-')
    output = []
    for speaker in speakers:
        for table in tables:
            if table in output: continue
            if speaker in table.speaker_ids: output.append(table)
    return output

def _handle_orignal_filename(filename, tables):
    '''helper function for filename to table for the original transcriptions.
    '''
    identifier = filename.split('/')[-1].split('.')[0]
    for table in tables:
        if identifier == table.identifier: return [table]


def open_transcription(filename):
    '''Open transcription text file and create Transcription object for each
    line.
    The transcription object can be used to find the corresponding turn
    This can be achieved by creating a Transcriptions object 
    '''
    with open(filename) as fin:
        t = [line.split('\t') for line in fin.read().split('\n') if line]
    output = []
    for index, line in enumerate(t):
        line[1] = float(line[1])
        line[3] = float(line[3])
        output.append(Transcription(line,index))
    return output

def get_section_wav_filenames(transcription_filename):
    fn = get_play_section_wav_filenames()
    name = transcription_filename.split('/')[-1].split('.')[0]
    output = []
    for f in fn:
        wav_name = f.split('/')[-1].split('_ch-')[0]
        if name == wav_name: output.append(f)
    return output
        
    

class Transcriptions:
    '''container object to hold all Transcription objects and match 
    corresponding turns.
    '''
    def __init__(self,filename, tables):
        self.transcription_filename = filename
        self.section_wav_filenames = get_section_wav_filenames(filename)
        self._make_speaker_to_channel_dict()
        self.tables = filename_to_tables(filename, tables)
        self.transcriptions = open_transcription(filename)
        self._find_turns()
        

    def __repr__(self):
        m = 'Transcriptions: ' + self.transcription_filename.split('/')[-1]
        m += ' ok: ' + str(self.ok)
        m += ' nturns: ' + str(len(self.transcriptions))
        return m

    def _make_speaker_to_channel_dict(self):
        fn = self.section_wav_filenames
        self.speaker_to_channel_dict = {}
        if 'DVA' in fn[0]: 
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
        for table in self.tables:
            self.all_turns.extend(table.turns)
        for transcription in self.transcriptions:
            transcription.find_turn(self.all_turns, self.excluded_turns)
            if transcription.ok: self.excluded_turns.append(transcription.turn)
        self.ok = len(self.excluded_turns) == len(self.transcriptions)
        

class Transcription:
    '''object to represent a line in a transcription text file
    can be used to match the line with a turn object to link data
    '''
    def __init__(self, line, index):
        self.line = line
        self.index = index
        self.speaker_id = line[0]
        self.start_time = line[1]
        self.end_time = line[3]
        self.text = line[2]

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

        


def get_play_section_wav_filenames():
    fn = glob.glob(locations.section_directory + '*.wav')
    return fn


