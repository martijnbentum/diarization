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
    def __init__(self, turns, output_filename='default.wav', overlap = False ): 
        self.turns = turns
        self.output_filename = output_filename
        self.overlap = overlap
        self.speaker_to_turns = turns_to_speaker_turn_dict(turns)
        self.ntracks = len(self.speaker_to_turns.keys())
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
            track = Track(channel, turns, speaker_id, self.output_filename)
            self.tracks.append(track)
            channel += 1

    def mix(self):
        '''mix speaker turns into non overlapping recording.'''
        self._make_track_order()
        for track in self.tracks:
            track.mix(self.track_order, self.turn_order)

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
        


class Track:
    '''object to contain audio for one channel.'''
    def __init__(self,channel, turns, speaker_id, output_filename):
        self.channel = channel
        self.turns = turns
        self.nturns = len(turns)
        self.speaker_id = speaker_id
        self.speaker = turns[0].speaker
        self.output_filename = output_filename
        self.current_index = 0
        self.padded_turns = []
        name, ext = output_filename.split('.')
        self.output_filename = name + '_channel-' + str(self.channel)
        self.output_filename += '.' + ext

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
            self.padded_turns.append(padded_turn)
        self.indices = indices
                
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
        return round(self.turn.duration + self.start + self.end,3)

    @property
    def start_time(self):
        return self.start

    @property
    def end_time(self):
        return self.turn.duration + self.start

    @property
    def sox_pad_cmd(self):
        cmd = '"|sox ' + self.wav_filename + ' -p pad '
        cmd += str(self.start) + ' ' + str(self.end) + '"'
        return cmd


def turns_to_speaker_turn_dict(turns):
    d = {}
    for turn in turns:
        if turn.speaker.id not in d.keys(): d[turn.speaker.id] =[]
        d[turn.speaker.id].append(turn)
    return d

def turns_to_duration(turns):
    return sum([t.duration for t in turns])
