import glob
import locations
import praatio
from praatio import textgrid
from praatio.utilities.constants import Interval
from praatio.data_classes import interval_tier

def all_text_files_to_textgrid(delta = 2):
    directory = locations.play_transcription_tables_directory
    fn = glob.glob(directory + '*.txt')
    textgrids = []
    for f in fn:
        filename_to_textgrid(f, delta)
    return textgrids

def filename_to_textgrid(filename, delta = 0):
    temp = filename.split('/')[-1].replace('.txt','.textgrid')
    output_filename = locations.play_textgrids_directory
    output_filename += temp
    text = load_text(filename)
    textgrid = text_to_textgrid(text, delta)
    textgrid.save(output_filename, 'short_textgrid', True)
    return textgrid

def text_to_textgrid(text, delta = 0):
    tg = textgrid.Textgrid()
    interval_dict = make_speaker_to_interval_dict(text, delta)
    for speaker, intervals in interval_dict.items():
        tier = interval_tier.IntervalTier(name = speaker, entries = intervals)
        tg.addTier(tier)
    return tg

def make_speaker_to_interval_dict(text, delta = 0):
    d = {}
    for line in text:
        speaker = line[0]
        if speaker not in d.keys(): d[speaker] = []
        interval = line_to_interval(line, delta)
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

def line_to_interval(line, delta = 0):
    start = float(line[1]) + delta
    label = line[2]
    end = float(line[3]) + delta
    return Interval(start,end,label)
