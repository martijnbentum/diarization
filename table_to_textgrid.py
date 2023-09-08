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

def filename_to_textgrid(filename, delta = 0, adjustment = 0,
    microphone_name = None):
    temp = filename.split('/')[-1].replace('.txt','.textgrid')
    if microphone_name: temp = microphone_name + '_' + temp
    output_filename = locations.sections_textgrid_directory
    output_filename += temp
    text = load_text(filename)
    textgrid = text_to_textgrid(text, delta, adjustment)
    textgrid.save(output_filename, 'short_textgrid', True)
    return textgrid

def text_to_textgrid(text, delta = 0, adjustment = 0):
    tg = textgrid.Textgrid()
    interval_dict=make_speaker_to_interval_dict(text,delta,adjustment)
    interval_dict = add_tones(interval_dict, delta, adjustment)
    for speaker, intervals in interval_dict.items():
        tier = interval_tier.IntervalTier(name = speaker, 
            entries = intervals)
        tg.addTier(tier)
    return tg

def make_speaker_to_interval_dict(text, delta = 0, adjustment = 0):
    d = {}
    for line in text:
        speaker = line[0]
        if speaker not in d.keys(): d[speaker] = []
        interval = line_to_interval(line, delta, adjustment)
        d[speaker].append(interval)
    return d

def add_tones(d, delta = 0, adjustment = 0):
    start = 0 + adjustment
    end = start + 1
    d['other'] = [Interval(start,end,'500hz 1 second start tone')]
    start = find_end_of_last_interval(d) + 1 + adjustment
    end = start + 1
    d['other'].append(Interval(start,end, '300hz 1 second end tone'))
    return d

def find_end_of_last_interval(interval_dict):
    end = 0
    for speaker, intervals in interval_dict.items():
        if speaker == 'other': continue
        for interval in intervals:
            if interval.end > end: 
                end = interval.end
    return end

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

def line_to_interval(line, delta = 0, adjustment = 0):
    start = float(line[1]) + delta + adjustment
    label = line[2]
    end = float(line[3]) + delta + adjustment
    return Interval(start,end,label)

# adjustments
def open_channel_info():
    filename = locations.recording_name_channels_filename
    t = open(filename).read().split('\n')
    d = dict([line.split('|') for line in t if line])
    channel_infos = {}
    for microphone_name, info in d.items():
        channels, selected, combined, processed = info.split(' ')
        channels = list(map(int,channels.split(',')))
        selected = int(selected)
        if combined == 'None': combined = None
        else: combined = int(combined)
        if processed == 'None': processed = None
        else: processed = int(processed)
        channel_infos[microphone_name] = {'channels':channels,
            'selected':selected,'combined':combined, 
            'processed':processed}
    return channel_infos

def wav_to_textgrid_filename(wav_filename, fn_textgrid):
    if 'DVA' in wav_filename:
        identifier = wav_filename.split('_')[-2] 
    else:
        identifier = '_spk-' + wav_filename.split('_')[-2] + '.textgrid'
    for f in fn_textgrid:
        if identifier in f: return f
    print('could not find textgrid filename with identifier:',identifier)

def textgrid_to_adjusted_filename(textgrid_filename, microphone_name):
    if not textgrid_filename: return
    f = textgrid_filename.split('/')[-1]
    d = locations.sections_adjustment_textgrid_directory
    adjusted_filename = d + microphone_name + '_' + f
    return adjusted_filename
    

def select_filenames(microphone_name, channel, fn_wav, fn_textgrid):
    d = {'microphone_name' : microphone_name, 'channel': channel}
    ch = str(channel)
    filenames = []
    for f in fn_wav:
        if not microphone_name in f: continue
        if not '_ch-' + ch + '.wav' in f: continue
        fd = {}
        fd['wav_filename'] = f
        fd['textgrid_filename'] = wav_to_textgrid_filename(f,fn_textgrid)
        fd['output_filename'] = textgrid_to_adjusted_filename(
            fd['textgrid_filename'], microphone_name)
        filenames.append(fd)
    d['filenames'] = filenames
    return d
        

def link_wav_and_textgrid_files(fn_wav = None, fn_textgrid = None):
    if not fn_wav:
        fn_wav = glob.glob(locations.sections_output_directory + '*.wav')
    if not fn_textgrid:
        d = locations.sections_textgrid_directory 
        fn_textgrid = glob.glob(d+'*.textgrid')
    channel_infos = open_channel_info()
    d = {}
    for microphone_name, info in channel_infos.items():
        channel = info['selected']
        d[microphone_name] = select_filenames(microphone_name, channel,
            fn_wav, fn_textgrid)
    return d
        
def read_template():
    with open(locations.base + 'adjustments_template') as fin:
        template = fin.read().split('\n')
    return template

def set_template(fd):
    template = read_template()
    template[0] = template[0] +'"'+ fd['textgrid_filename']+'"'
    template[1] = template[1] +'"'+ fd['wav_filename']+'"'
    template[2] = template[2] +'"'+ fd['output_filename']+'"'
    return template

def make_adjustment_script(link_dictionary = None, save = False):
    if not link_dictionary: link_dictionary = link_wav_and_textgrid_files()
    output = ['writeInfoLine: "start"']
    for microphone_name, info in link_dictionary.items():
        for fd in info['filenames']:
            if not fd['output_filename']: 
                print('no textgrid, skipping:',fd)
                continue
            template = set_template(fd)
            output.extend(template)
    if save:
        with open(locations.base + 'adjust_all_textgrids.praat','w') as fout:
            fout.write('\n'.join(output))
    return output

