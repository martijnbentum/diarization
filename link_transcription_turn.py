import glob
import handle_phrases

def make_filename_to_transcriptions_dict(tables = None, directory = None):
    if not tables: 
        Tables = handle_phrases.Tables()
        tables = Tables.tables
    d = {}
    fn = get_mix_filenames(directory)
    for filename in fn:
        d[filename] = Transcriptions(filename, tables)
    return d

def make_filename_tables_dict(tables = None, directory = None):
    if not tables: 
        Tables = handle_phrases.Tables()
        tables = Tables.tables
    fn = get_mix_filenames(directory)
    d = {}
    for filename in fn:
        d[filename] = filename_to_tables(filename, tables)
    return d

def get_mix_filenames(directory = None):
    if not directory: directory = '../PLAY_TRANSCRIPTION_TABLES/'
    return glob.glob(directory + '*.txt')

def filename_to_tables(filename, tables):
    if 'nch' in filename: return _handle_mix_filename(filename, tables)
    if 'DVA' in filename: return _handle_orignal_filename(filename, tables)

def _handle_mix_filename(filename,tables):
    speakers = filename.split('spk-')[-1].split('.')[0].split('-')
    output = []
    for speaker in speakers:
        for table in tables:
            if table in output: continue
            if speaker in table.speaker_ids: output.append(table)
    return output

def _handle_orignal_filename(filename, tables):
    identifier = filename.split('/')[-1].split('.')[0]
    for table in tables:
        if identifier == table.identifier: return [table]


def open_transcription(filename):
    with open(filename) as fin:
        t = [line.split('\t') for line in fin.read().split('\n') if line]
    output = []
    for index, line in enumerate(t):
        line[1] = float(line[1])
        line[3] = float(line[3])
        output.append(Transcription(line,index))
    return output

class Transcriptions:
    def __init__(self,filename, tables):
        self.filename = filename
        self.tables = filename_to_tables(filename, tables)
        self.transcriptions = open_transcription(filename)
        self._find_turns()

    def __repr__(self):
        m = 'Transcriptions: ' + self.filename
        m += ' ok: ' + str(self.ok)
        m += ' nturns: ' + str(len(self.transcriptions))
        return m

    def _find_turns(self):
        self.all_turns = []
        self.excluded_turns = []
        for table in self.tables:
            self.all_turns.extend(table.turns)
        for transcription in self.transcriptions:
            transcription.find_turn(self.all_turns, self.excluded_turns)
            if transcription.ok: self.excluded_turns.append(transcription.turn)
        self.ok = len(self.excluded_turns) == len(self.transcriptions)
        

class Transcription:
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

        


