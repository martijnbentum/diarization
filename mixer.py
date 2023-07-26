import handle_phrases as ph
import glob
import ifadv_clean as ic
import os
import random

random.seed(9)

home_dir = os.path.expanduser('~') + '/'
# output_dir = home_dir + 'mixed_audio/'
output_dir = '/Volumes/Expansion/third_recording_session/'
output_tone_dir = '/Volumes/Expansion/third_recording_session_tone/'

def add_audio_id_start_and_end_tone(audio_id_filename, mix_filename, output_filename):
    cmd = 'sox ' + audio_id_filename + ' '
    cmd +=  '../TONE/start_tone.wav '
    cmd += mix_filename + ' '
    cmd += '../TONE/end_tone.wav '
    cmd += output_filename 
    os.system(cmd)
    return cmd

def make_audio_ids():
    fn = glob.glob('../RANDOM_WORDS/*.wav')
    for f in fn:
        make_identifier_audio_file(f, f.replace('../RANDOM_WORDS/','../AUDIO_ID/'))

def make_identifier_audio_file(input_filename, output_filename):
    cmd = 'sox --combine sequence'
    cmd += ' "|sox ../TONE/tone_700.wav -p pad 1 1"'
    cmd += ' "|sox ' + input_filename + ' -p pad 1 1"'
    cmd += ' "|sox ../TONE/tone_700.wav -p pad 0 1"'
    cmd += ' -b 16 ' + output_filename
    print(cmd)
    os.system(cmd)
    return cmd

def make_tone(frequency = 500):
    filename = '../TONE/tone_' + str(frequency) + '.wav'
    cmd = 'sox -b 16 -n ' + filename +' synth 1 sine ' + str(frequency)
    cmd += ' vol 0.3'
    os.system(cmd)
    return cmd

def make_start_tone():
    combine_tones([500,500])
    os.system('cp ../TONE/sequence_500-500.wav ../TONE/start_tone.wav')

def make_end_tone():
    combine_tones([300,300])
    os.system('cp ../TONE/sequence_300-300.wav ../TONE/end_tone.wav')

def combine_tones(frequencies = [500,300]):
    cmd = 'sox --combine sequence'
    for i,frequency in enumerate(frequencies):
        f = '../TONE/tone_' + str(frequency) + '.wav'
        if not f: make_tone(frequency)
        if i == 0: 
            cmd +=' "| sox ' + f + ' -p pad 1 2"'
        elif i == len(frequencies) - 1:
            cmd +=' "| sox ' + f + ' -p pad 0 1"'
        else:
            cmd +=' "| sox ' + f + ' -p pad 0 2"'
    filename = '../TONE/sequence_' + '-'.join(map(str,frequencies)) + '.wav'
    cmd += ' -b 16 ' + filename 
    os.system(cmd)
    return cmd

def add_start_tone(input_filename, output_filename):
    cmd = 'sox start_tone.wav ' + input_filename + ' ' + output_filename
    os.system(cmd)
    return cmd

def check_files_exist(filenames):
    for filename in filenames:
        if not os.path.isfile(filename):
            raise ValueError(filename, 'does not exist')

def cmd_concatenate_audio_files(filenames, silences, output_filename):
    '''add audio files sequentially on same channel.'''
    assert len(filenames) == len(silences)
    assert not os.path.isfile(output_filename)
    check_files_exist(filenames)
    cmd = 'sox --combine sequence '
    for filename, silence in zip(filenames, silences):
        pad = ' -p pad 0 ' + str(silence) 
        cmd += '"|sox ' + filename + pad + '" '
    cmd += '-b 16 ' + output_filename 
    return cmd
        
def cmd_combine_audio_files_to_multi_track(filenames,output_filename,mono=False):
    assert not os.path.isfile(output_filename)
    check_files_exist(filenames)
    if mono: m = ' -m '
    else: m = '-M '
    cmd = 'sox' + m + ' '.join(filenames)
    cmd += ' ' + output_filename
    return cmd

class Tracks:
    '''object to hold multiple tracks to be mixed in multi track audio.'''
    def __init__(self, turns, output_filename= '', overlap = False ): 
        self.turns = check_audio_file_turns(turns)
        print(len(self.turns), 'len turns')
        self.overlap = overlap
        self.speaker_to_turns = turns_to_speaker_turn_dict(self.turns)
        self.ntracks = len(self.speaker_to_turns.keys())
        self._set_output_filename(output_filename)
        self.nturns = len(turns)
        self._add_tracks()
        self.mix()

    def __repr__(self):
        m = 'speakers: ' + ', '.join(list(self.speaker_to_turns.keys()))
        m += ' | nchannels: ' + str(self.ntracks)
        return m

    def _add_tracks(self):
        '''create a track for each distinct speaker in the list of turns'''
        self.tracks = []
        channel = 1
        for speaker_id, turns in self.speaker_to_turns.items():
            track = Track(channel, turns, speaker_id, self)
            self.tracks.append(track)
            channel += 1

    def mix(self):
        '''mix speaker turns into non overlapping recording.'''
        if self.overlap: return self._mix_overlap()
        self._make_track_order()
        for track in self.tracks:
            track.mix(self.track_order, self.turn_order)

    def _mix_overlap(self):
        self.turn_order = []
        for track in self.tracks:
            self.turn_order.extend(track.turns)
            track.mix_overlap()

    def _make_track_order(self):
        '''create order of speaker turns.'''
        self.track_order = []
        self.turn_order = []
        last_track = None
        for i in range(self.nturns):
            track_set = [track for track in self.tracks if track != last_track]
            track = random.sample(track_set, 1)[0]
            turn = track.get_next_turn()
            if turn:
                self.track_order.append(track)
                self.turn_order.append(turn)
                last_track = track

    def _set_output_filename(self, output_filename):
        if output_filename: self.output_filename = output_filename
        n = ''
        if self.overlap: n += 'overlap_'
        n += 'nch-' + str(self.ntracks)
        n += '_spk-' + '-'.join(list(self.speaker_to_turns.keys()))
        n += '.wav'
        self.output_filename = output_dir + n


    def channel_to_track(self, channel):
        '''get track based on channel number.'''
        track = self.tracks[channel-1]
        assert track.channel == channel
        return channel
        
    def turn_to_track(self,turn):
        '''get track based on turn.'''
        for track in self.tracks:
            if track.holds_turn(turn): return track
        raise ValueError(turn, 'not found in any track')

    def make(self):
        if self.overlap: return self._make_overlap()
        for track in self.tracks:
            track.make()
        self.save_table()
        self.make_mono()

    def _make_overlap(self):
        for track in self.tracks:
            track.make_overlap()
        self.save_table()
        

    def make_mono(self):
        fn = []
        for track in self.tracks:
            if not os.path.isfile(track.output_filename): 
                raise ValueError('non all audio tracks available',
                    track.output_filename)
            fn.append(track.output_filename)
        path = self.output_filename.split('/')[0]
        output_filename = self.output_filename.split('/')[-1]
        name,ext = output_filename.split('.')
        f = path + name + '_mono.' + ext
        if os.path.isfile(f) and f.endswith('.wav'): os.system('rm ' + f)
        cmd = cmd_combine_audio_files_to_multi_track(fn,f, mono=True)
        print('make mono file with sox command: ',cmd)
        os.system(cmd)


    def save_table(self):
        f = self.output_filename.replace('.wav','.txt')
        with open(f,'w') as fout:
            fout.write('\n'.join(self.table_lines()))

    @property
    def padded_turns(self):
        o = []
        for turn in self.turn_order:
            o.append(turn.padded_turn)
        return o
            
    def table_lines(self):
        table_lines = []
        for pt in self.padded_turns:
            table_lines.append(pt.table_line)
        return table_lines
        


class Track:
    '''object to contain audio for one channel.'''
    def __init__(self,channel, turns, speaker_id, tracks):
        self.channel = channel
        self.turns_raw = turns
        self._prune_turns_without_filename()
        self.nturns = len(self.turns)
        self.speaker_id = speaker_id
        self.tracks = tracks
        self.speaker = turns[0].speaker
        self.output_filename = tracks.output_filename
        self.current_index = 0
        self.padded_turns = []
        name, ext = self.output_filename.split('.')
        self.output_filename = name + '_ch-' + str(self.channel)
        self.output_filename += '_spk-' + self.speaker.id
        self.output_filename += '.' + ext
        print(speaker_id,len(self.turns))

    def _prune_turns_without_filename(self):
        self.turns = []
        for turn in self.turns_raw:
            if not os.path.isfile(turn.wav_filename): continue
            self.turns.append(turn)
        self.turns = self.turns[:250]

    def __eq__(self,other):
        if type(self) != type(other): return False
        return self.channel == other.channel

    def __repr__(self):
        m = 'channel: ' + str(self.channel)
        m += ' | nturns: ' + str(len(self.turns))
        m += ' | speaker: ' + self.speaker_id
        return m

    def holds_turn(self,turn):
        return turn in self.turns

    @property
    def duration(self):
        return round(sum([pt.duration for pt in self.padded_turns]),3)

    def get_next_turn(self):
        if self.current_index >= self.nturns: return
        turn = self.turns[self.current_index]
        self.current_index += 1
        return turn

    def mix(self,track_order, turn_order):
        indices = self._get_indices(track_order)
        for i,index in enumerate(indices):
            turn = turn_order[index]
            if i == 0 and index != 0:
                turns = turn_order[:index]
                start_pad = turns_to_duration(turns)
            else: start_pad = 0
            if i + 1 >= len(indices): 
                if index < len(turn_order) -1:
                    end_pad = turns_to_duration(turn_order[index+1:])
                else:
                    end_pad = 0 
            else:
                turns = turn_order[index + 1: indices[i+1]]
                end_pad = turns_to_duration(turns)
            padded_turn = Padded_turn(start_pad, end_pad, turn, self)
            turn.padded_turn = padded_turn
            self.padded_turns.append(padded_turn)
        self.indices = indices

    def mix_overlap(self):
        for turn in self.turns:
            padded_turn = Padded_turn(0,0, turn, self)
            turn.padded_turn = padded_turn
            self.padded_turns.append(padded_turn)

                
    def _get_indices(self,track_order):
        indices = []
        for i, track in enumerate(track_order):
            if track == self: indices.append(i)
        return indices

    @property
    def sox_pad_cmd(self):
        cmd = 'sox --combine sequence '
        cmd += ' '.join([pt.sox_pad_cmd for pt in self.padded_turns])
        cmd += ' -b 16 ' + self.output_filename
        return cmd

    @property
    def overlap_sox_cmd(self):
        fn = turns_to_filenames(self.turns)
        if os.path.isfile(self.output_filename):
            if self.output_filename.endswith('.wav'):
                os.system('rm ' + self.output_filename)
        return 'sox ' + ' '.join(fn) + ' -b 16 ' + self.output_filename

    @property
    def table_lines(self):
        table_lines = []
        for pt in self.padded_turns:
            table_lines.append(pt.table_line)
        return table_lines
            

    def make(self):
        print('saving audio mixed file', self.output_filename)
        os.system(self.sox_pad_cmd)

    def make_overlap(self):
        print('saving audio overlap file', self.output_filename)
        os.system(self.overlap_sox_cmd)
    

    
       


class Padded_turn:
    def __init__(self,start,end, turn, track):
        self.start = start
        self.end = end
        self.turn = turn
        self.track = track
        self.turn_id = turn.turn_id
        self.wav_filename = turn.wav_filename

    def __repr__(self):
        return 'padded turn: ' + self.turn_id

    def add_to_start(self,seconds):
        self.start += seconds

    def add_to_end(self,seconds):
        self.end += seconds

    @property
    def duration(self):
        return self.turn.duration + self.start + self.end

    @property
    def start_time(self):
        if self.track.tracks.overlap:
            turn_order = self.track.turns
        else:
            turn_order = self.track.tracks.turn_order
        i = turn_order.index(self.turn)
        start_time = sum([turn.duration for turn in turn_order[:i]])
        return round(start_time,3)

    @property
    def end_time(self):
        return round(self.start_time + self.turn.duration ,3)

    @property
    def sox_pad_cmd(self):
        cmd = '"|sox ' + self.wav_filename + ' -p pad '
        cmd += str(self.start) + ' ' + str(self.end) + '"'
        return cmd

    @property
    def table_line(self):
        l = self.turn.speaker.id + '\t'
        l += str(self.start_time) + '\t'
        l += self.turn.text + '\t'
        l += str(self.end_time)
        return l
        

def turns_to_speaker_turn_dict(turns):
    d = {}
    for turn in turns:
        if turn.speaker.id not in d.keys(): d[turn.speaker.id] =[]
        d[turn.speaker.id].append(turn)
    return d

def turns_to_duration(turns):
    return sum([t.duration for t in turns])

def turns_to_filenames(turns):
    fn = []
    turns = check_audio_file_turns(turns)
    return [t.wav_filename for t in turns]

def shortest_track_duration(tracks):
    shortest = 10**9
    for track in tracks:
        duration = turns_to_duration(track.turns)
        if duration < shortest: shortest = duration
    return shortest
        
def check_audio_file_turns(turns):
    output = []
    for turn in turns:
        if os.path.isfile(turn.wav_filename):
            output.append(turn)
    return output
        
