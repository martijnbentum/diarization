import glob
import locations
import praatio
from praatio import textgrid
from praatio.utilities.constants import Interval
from praatio.data_classes import interval_tier

def all_text_files_to_textgrid(delta = 2):
    '''create textgrids for all audio sections 
    the textgrids are not adjusted for inaccuracies of the audio section
    extractions. These adjustments are microphone specific.
    '''
    directory = locations.play_transcription_tables_directory
    fn = glob.glob(directory + '*.txt')
    textgrids = []
    for f in fn:
        filename_to_textgrid(f, delta)
    return textgrids

def _get_adjustment_infos(f, adjustments_dict):
    name = f.split('/')[-1].split('.')[0]
    output = []
    for k, v in adjustments_dict.items():
        if name in k: output.append(v)
    return output

def make_all_adjusted_textgrids(delta = 2, adjustment_dict = None):
    '''create microphone specific textgrids aligned with the extracted audio.
    the adjustments are based and the adjustment dict created by the function
    read_adjustment_textgrids
    the adjustment values where manually assessed based on the start tone.
    '''
    if not adjustment_dict:
        adjustment_dict, _ = read_adjustment_textgrids()
    directory = locations.play_transcription_tables_directory
    fn = glob.glob(directory + '*.txt')
    for f in fn:
        infos = _get_adjustment_infos(f, adjustment_dict)
        for info in infos:
            print(info['identifier'])
            adjustment = info['adjustment']
            microphone_name = info['microphone_name']
            filename_to_textgrid(f, delta, adjustment,microphone_name)

def filename_to_textgrid(filename, delta = 0, adjustment = 0,
    microphone_name = None):
    '''create a textgrid based on a table file with start and end times
    for each speaker in the audio section
    delta       the audio duration in secionds pre- and appended before the 
                start and after the end of the speech
    adjustment  the time in seconds to shift annotations to align it with
                the audio file to correct for inaccuracies of extracting the
                audio from the long recording which was automatically
                determined based on the start tone.
    micropho... the name of the microphone recording the textgrid 
                corresponds to
    '''
    temp = filename.split('/')[-1].replace('.txt','.textgrid')
    if microphone_name: temp = microphone_name + '_' + temp
    output_filename = locations.sections_textgrid_directory
    output_filename += temp
    text = load_text(filename)
    textgrid = text_to_textgrid(text, delta, adjustment)
    textgrid.save(output_filename, 'short_textgrid', True)
    return textgrid

def text_to_textgrid(text, delta = 0, adjustment = 0):
    '''create a textgrid based on a table file with start and end times
    orthographic annotation and speaker label.
    the table files can be found in the 
    locations.play_transcription_tables_directory
    '''
    tg = textgrid.Textgrid()
    interval_dict=make_speaker_to_interval_dict(text,delta,adjustment)
    interval_dict = add_tones(interval_dict, delta, adjustment)
    for speaker, intervals in interval_dict.items():
        tier = interval_tier.IntervalTier(name = speaker, 
            entries = intervals)
        tg.addTier(tier)
    return tg

def make_speaker_to_interval_dict(text, delta = 0, adjustment = 0):
    '''create a dictionary that maps a speaker to all his or her intervals.'''
    d = {}
    for line in text:
        speaker = line[0]
        if speaker not in d.keys(): d[speaker] = []
        interval = line_to_interval(line, delta, adjustment)
        d[speaker].append(interval)
    return d

def add_tones(d, delta = 0, adjustment = 0):
    '''add a tier "other" that annotates the start and end tone.
    the tier is also used to record adjustment for aligning audio with 
    transcription
    '''
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

def textgrid_to_adjustment_filename(textgrid_filename, microphone_name):
    '''create filename for textgrid to annotate adjustment value
    to correct alignment between audio and textgrid
    of the automatically extracted audio based on start tone.
    '''
    if not textgrid_filename: return
    f = textgrid_filename.split('/')[-1]
    d = locations.sections_adjustment_textgrid_directory
    adjustment_filename = d + microphone_name + '_' + f
    return adjustment_filename
    

def select_filenames(microphone_name, channel, fn_wav, fn_textgrid):
    '''create a dictionary that links the audio filename with different
    textgrid filenames'''
    d = {'microphone_name' : microphone_name, 'channel': channel}
    ch = str(channel)
    filenames = []
    for f in fn_wav:
        if not microphone_name in f: continue
        if not '_ch-' + ch + '.wav' in f: continue
        fd = {}
        fd['wav_filename'] = f
        fd['textgrid_filename'] = wav_to_textgrid_filename(f,fn_textgrid)
        fd['adjustment_filename'] = textgrid_to_adjustment_filename(
            fd['textgrid_filename'], microphone_name)
        filenames.append(fd)
    d['filenames'] = filenames
    return d
        

def link_wav_and_textgrid_files(fn_wav = None, fn_textgrid = None):
    '''create a dictionary that links the microphone name to all audio files
    and corresponding textgrid files.
    '''
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
    '''reads the praat template to create the praat adjustment script.'''
    with open(locations.base + 'adjustments_template') as fin:
        template = fin.read().split('\n')
    return template

def set_template(fd):
    '''set the specific file information in the praat script template.'''
    template = read_template()
    template[0] = template[0] +'"'+ fd['textgrid_filename']+'"'
    template[1] = template[1] +'"'+ fd['wav_filename']+'"'
    template[2] = template[2] +'"'+ fd['adjustment_filename']+'"'
    return template

def make_adjustment_script(link_dictionary = None, save = False):
    '''create a praat script based on a template to make alignment adjustment.
    audio sections where extracted from the long recording based on a start 
    tone and there is some error which needs to be corrected.
    the generate praat script loads and audio section and corresponding textgrid
    based on the tone and adjustment value in seconds can be entered in 
    the second interval of the other tier.
    A new textgrid can be generated based on the adjustment value
    These textgrids will be specific for a given microphone
    '''
    if not link_dictionary: link_dictionary = link_wav_and_textgrid_files()
    output = ['writeInfoLine: "start"']
    for microphone_name, info in link_dictionary.items():
        for fd in info['filenames']:
            if not fd['adjustment_filename']: 
                print('no textgrid, skipping:',fd)
                continue
            template = set_template(fd)
            output.extend(template)
    if save:
        with open(locations.base + 'adjust_all_textgrids.praat','w') as fout:
            fout.write('\n'.join(output))
    return output

def _get_microphone_name(name):
    if 'minidsp' in name: return 'minidsp'
    if 'grensvlak' in name: return 'grensvlak'
    if 'shure' in name: return 'shure'
    if 'left_respeaker' in name: return 'left_respeaker'
    if 'right_respeaker' in name: return 'right_respeaker'
    raise ValueError(name,'does not contain expected microphone name')

def read_adjustment_textgrids():
    '''Reads the textgrids with the adjustment values.
    returns a dictionary with adjustment value for each microphone section
    combination
    '''
    fn=glob.glob(locations.sections_adjustment_textgrid_directory+ '*.textgrid')
    adjustments ={}
    for f in fn:
        d = {'path':f}
        name = f.split('/')[-1]
        identifier = name.split('.')[0]
        d['name'] = name
        d['microphone_name'] = _get_microphone_name(name)
        d['identifier'] = identifier
        tg = textgrid.openTextgrid(f,False)
        tier = tg.getTier('other')
        d['adjustment'] = round(float(tier.entries[1].label) - 1,6)
        adjustments[identifier] = d
    return adjustments

        

