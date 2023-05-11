import handle_phrases as ph
import ifadv_clean as ic
import os
import random

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
        
def cmd_combine_audio_files_to_multi_track(filenames,output_filename):
    assert not os.path.isfile(output_filename)
    check_files_exist(filenames)
    cmd = 'sox -M ' + ' '.join(filenames)
    cmd += ' ' + output_filename
    return cmd


class Tracks:
    '''object to hold multiple tracks to be mixed in multi track audio.'''
    def __init__(self, turns, overlap = False): 
        self.turns = turns
        self.overlap = overlap
        self.speaker_to_turns = turns_to_speaker_turn_dict(turns)
        self.ntracks = len(self.speaker_to_turns.keys())
        self.nturns = len(turns)
        self._add_tracks()

    def __repr__(self):
        m = 'speakers: ' + ', '.join(list(self.speaker_to_turns.keys()))
        m += ' | nchannels: ' + str(self.ntracks)
        return m

    def _add_tracks(self):
        '''create a track for each distinct speaker in the list of turns'''
        self.tracks = []
        channel = 1
        for speaker_id, turns in self.speaker_to_turns.items():
            self.tracks.append(Track(channel, turns, speaker_id))
            channel += 1

    def mix(self):
        '''mix speaker turns into non overlapping recording.'''
        self._make_track_order()
        for i,track in enumerate(self.track_order):
            if track.done: continue
            other_tracks = [t for t in self.tracks if t != track]
            duration = track.turn.duration
            if i == 0: pad_start(other_tracks, duration)
            else: 
                pad_end(other_tracks, duration)
                track.add_padded_turn()
            print(i,track.channel,len(track.padded_turns))
            

    def _make_track_order(self):
        '''create order of speaker turns.'''
        self.track_order = []
        last_track = None
        for i in range(self.nturns):
            track_set = [track for track in self.tracks if track != last_track]
            track = random.sample(track_set, 1)[0]
            self.track_order.append(track)
            last_track = track

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


def pad_start(other_tracks, duration):
    for track in other_tracks:
        track.padded_turn.add_to_start(duration)
def pad_end(other_tracks, duration):
    for track in other_tracks:
        if not track.done:
            track.padded_turn.add_to_end(duration)
        else: 
            track.padded_turns[-1].add_to_end(duration)
        


class Track:
    '''object to contain audio for one channel.'''
    def __init__(self,channel, turns, speaker_id):
        self.channel = channel
        self.turns = turns
        self.nturns = len(turns)
        self.speaker_id = speaker_id
        self.speaker = turns[0].speaker
        self.current_index = 0
        self.padded_turns = []
        self.make_padded_turn()
        self.done = False

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

    def make_padded_turn(self, start = 0):
        if self.current_index >= self.nturns:
            self.padded_turn = None
            self.turn = None
            self.done = True
        else:
            self.turn = self.turns[self.current_index]
            self.padded_turn = Padded_turn(0, 0, self.turn, self)

    def add_padded_turn(self):
        if self.done:
            print(track,'cannot add padded turn, track done, no more turns')
            return
        self.padded_turns.append(self.padded_turn)
        self.current_index += 1
        self.make_padded_turn()

    @property
    def duration(self):
        return round(sum([pt.duration for pt in self.padded_turns]),3)


class Padded_turn:
    def __init__(self,start,end, turn, track):
        self.start = start
        self.end = end
        self.turn = turn
        self.track = track
        self.turn_id = turn.wav_filename.split('/')[-1].split('.')[0]

    def __repr__(self):
        return 'padded turn: ' + self.turn_id

    def add_to_start(self,seconds):
        self.start += seconds

    def add_to_end(self,seconds):
        self.end += seconds

    @property
    def duration(self):
        return round(self.turn.duration + self.start + self.end,3)

    @property
    def start_time(self):
        return self.start

    @property
    def end_time(self):
        return self.turn.duration + self.start


def turns_to_speaker_turn_dict(turns):
    d = {}
    for turn in turns:
        if turn.speaker.id not in d.keys(): d[turn.speaker.id] =[]
        d[turn.speaker.id].append(turn)
    return d

def turns_to_duration(turns):
    return sum([t.duration for t in turns])
