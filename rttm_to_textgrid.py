import glob
import locations
import os
from pathlib import Path

from praatio import textgrid
from praatio.utilities.constants import Interval
from praatio.data_classes import interval_tier
import random

fn = glob.glob(locations.rttm_directory + '*.rttm')

def open_rttm(filename):
    with open(filename, 'r') as f:
        lines = f.read().split('\n')
    o = [x.split(' ') for x in lines]
    return o

class Rttm:
    def __init__(self,filename):
        self.filename = filename
        self.t = open_rttm(filename)
        self._set_info()

    def _set_info(self):
        self.words = [Word(x) for x in self.t if x and len(x) == 10 ]
        self.error = [x for x in self.t if len(x) != 10]
        self.turns = []
        last_speaker = self.words[0].speaker
        start_index = 0
        last_end = 0
        new_turn = False
        turn_duration = 0
        for i, w in enumerate(self.words):
            w.index = i
            if i > 0:
                start_word = self.words[start_index]
                last_word = self.words[i-1]
                turn_duration = last_word.end - start_word.start 
            if last_speaker != w.speaker: new_turn = True
            if last_end - w.start > 1: new_turn = True
            if turn_duration > 2: new_turn = True
            print(turn_duration)
            if new_turn:
                self.turns.append(Turn(start_index,i,self))
                last_speaker = w.speaker
                start_index = i
                new_turn = False

    @property
    def speaker_turn_dict(self):
        d = {}
        for t in self.turns:
            if t.speaker not in d:
                d[t.speaker] = []
            d[t.speaker].append(t)
        return d

    @property
    def speaker_word_dict(self):
        d = {}
        for w in self.words:
            if w.speaker not in d:
                d[w.speaker] = []
            d[w.speaker].append(w)
        return d

    def textgrid_with_words(self):
        tg = textgrid.Textgrid()
        for speaker, words in self.speaker_word_dict.items():
            tier = interval_tier.IntervalTier(name = speaker, 
                entries = [word.interval for word in words])
            tg.addTier(tier)
        return tg
            
    @property
    def textgrid(self):
        tg = textgrid.Textgrid()
        for speaker, turns in self.speaker_turn_dict.items():
            tier = interval_tier.IntervalTier(name = speaker, 
                entries = [turn.interval for turn in turns])
            tg.addTier(tier)
        return tg

    def save_textgrid(self, filename = None, with_words = False):
        if not filename:
            if with_words: ext = '_with_words.TextGrid'
            else: ext = '_turns.TextGrid'
            filename = self.filename.replace('.rttm',ext)
        if with_words: tg = self.textgrid_with_words()
        else: tg = self.textgrid
        tg.save(filename, 'short_textgrid',True)
            
        
class Turn:
    def __init__(self,start_index, end_index, rttm):
        self.start_index = start_index
        self.end_index = end_index
        self.rttm = rttm
        self.words = rttm.words[start_index:end_index]
        self.start = round(self.words[0].start,3)
        self.end = round(self.words[-1].end,3)
        self.duration = self.end - self.start
        self.speaker = self.words[0].speaker
        self.turn = ' '.join([x.word for x in self.words])
        self.check()

    def check(self):
        self.ok = True
        for word in self.words:
            if word.speaker != self.speaker:
                self.ok = False

    def __repr__(self):
        m = '{} | {} | {}'.format(self.speaker, self.turn, self.start)
        return m

    @property
    def interval(self):
        return Interval(self.start, self.end, self.turn)

class Word:
    def __init__(self,line):
        self.line = line
        self.name = line[1]
        self.start = float(line[3])
        self.duration = float(line[4])
        self.end = self.start + self.duration
        self.speaker = line[7]
        self.word = line[9]

    def __repr__(self):
        m = '{} | {} | {}'.format(self.speaker,self.word, self.start)
        return m


    @property
    def interval(self):
        return Interval(round(self.start,3), round(self.end,3), self.word)


def select_turns(rttm, speaker, n =300):
    turns = [x for x in rttm.turns if x.speaker == speaker and x.ok]
    turns = turns[2:-2]
    if len(turns) < n: n = len(turns)
    return random.sample(turns,n)

def make_turn_name(turn):
    filename = Path(turn.rttm.filename).stem
    return '{}__{}__{}'.format(filename,turn.speaker, turn.start_index)

def extract_audio(turn,input_wav_filename,output_directory):
    name = make_turn_name(turn)
    output_wav_filename = output_directory + name + '.wav'
    cmd = 'sox ' + input_wav_filename + ' ' + output_wav_filename + ' '
    cmd += 'trim ' + str(turn.start)
    cmd += ' ' + str(turn.duration)
    print(cmd)
    os.system(cmd)

def extract_text(turn,output_directory):
    name = make_turn_name(turn)
    output_text_filename = output_directory + name + '.txt'
    text =turn.interval.label + ' <{}> <{}> <{}> <{}>'.format(turn.speaker,
        turn.start, turn.end, round(turn.duration,2))
    print(text)
    with open(output_text_filename,'w') as f:
        f.write(text)

def make_segments(rttm, input_wav_filename, output_directory, speakers, n=100):
    for speaker in speakers:
        turns = select_turns(rttm,speaker,n)
        for turn in turns:
            extract_audio(turn,input_wav_filename,output_directory)
            extract_text(turn,output_directory)


