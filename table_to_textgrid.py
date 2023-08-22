import glob
import praatio
from praatio import textgrid
from praatio.utilities.constants import Interval
from praatio.data_classes import interval_tier

def all_text_files_to_textgrid():
    fn = glob.glob('../PLAY_TRANSCRIPTION_TABLES/*.txt')
    textgrids = []
    for f in fn:
        filename_to_textgrid(f)
    return textgrids

def filename_to_textgrid(filename):
    output_filename = filename.split('/')[-1].replace('.txt','.textgrid')
    output_filename = '../PLAY_TEXTGRIDS/' + output_filename
    text = load_text(filename)
    textgrid = text_to_textgrid(text)
    textgrid.save(output_filename, 'short_textgrid', True)
    return textgrid

def text_to_textgrid(text):
    tg = textgrid.Textgrid()
    interval_dict = make_speaker_to_interval_dict(text)
    for speaker, intervals in interval_dict.items():
        tier = interval_tier.IntervalTier(name = speaker, entries = intervals)
        tg.addTier(tier)
    return tg

def make_speaker_to_interval_dict(text):
    d = {}
    for line in text:
        speaker = line[0]
        if speaker not in d.keys(): d[speaker] = []
        interval = line_to_interval(line)
        d[speaker].append(interval)
    return d

def load_text(filename):    
    with open(filename) as fin:
        t = fin.read().split('\n')
    return [line.split('\t') for line in t]

def phrase_to_interval(phrase):
    label = phrase.text
    start = phrase.start_time
    end = phrase.end_time
    return Interval(start,end,label)

def turn_to_interval(turn):
    return phrase_to_interval(turn)

def line_to_interval(line):
    start = float(line[1])
    label = line[2]
    end = float(line[3])
    return Interval(start,end,label)
