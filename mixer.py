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
        self._add_tracks()

    def __repr__(self):
        m = 'speakers: ' + ', '.join(list(self.speaker_to_turns.keys()))
        m += ' | nchannels: ' + str(self.ntracks)
        return m

    def _add_tracks(self):
        self.tracks = []
        channel = 1
        for speaker_id, turns in self.speaker_to_turns.items():
            self.tracks.append(Track(channel, turns, speaker_id))
            channel += 1

    def mix(self):
        self.shuffle_turns = self.turns[:]
        random.shuffle(self.shuffle_turns)
        


class Track:
    '''object to contain audio for one channel.'''
    def __init__(self,channel, turns, speaker_id):
        self.channel = channel
        self.turns = turns
        self.speaker_id = speaker_id
        self.speaker = turns[0].speaker

    def __repr__(self):
        m = 'channel: ' + str(self.channel)
        m += ' | nturns: ' + str(len(self.turns))
        m += ' | speaker: ' + self.speaker_id
        return m


class Padded_turn:
    def __init__(self,start,end, turn):
        self.start = start
        self.end = end
        self.turn = turn
        self.turn_id = turn.wav_filename.split('/')[-1].split('.')

    def __repr__(self):
        return 'padded turn: ' + self.turn_id

    def add_to_start(seconds):
        self.start += seconds

    def add_to_end(seconds):
        self.end += seconds


def turns_to_speaker_turn_dict(turns):
    d = {}
    for turn in turns:
        if turn.speaker.id not in d.keys(): d[turn.speaker.id] =[]
        d[turn.speaker.id].append(turn)
    return d

def turns_to_duration(turns):
    return sum([t.duration for t in turns])
