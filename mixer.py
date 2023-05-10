import handle_phrases as ph
import ifadv_clean as ic

def concatenate_audio_files(filenames, silences, output_filename = 'default.wav'):
    assert len(filenames) == len(silences)
    cmd = 'sox --combine sequence '
    for filename, silence in zip(filenames, silences):
        pad = ' -p pad 0 ' + str(silence) 
        cmd += '"|sox ' + filename + pad + '" '
    cmd += '-b 16 ' + output_filename 
    return cmd
        


class Tracks:
    def __init__(self, turns): 
        self.turns = turns



class Track:
    def __init__(self,channel, turns, speaker):
        self.channel = channel
        self.turns = turns
        self.speaker = speaker


def turns_to_speaker_turn_dict(turns):
    d = {}
    for turn in turns:
        if turn.speaker.id not in d.keys(): d[turn.speaker.id] =[]
            d[turn.speaker.id].append(turn)
    return d
