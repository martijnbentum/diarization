import rttm_to_textgrid as rttm
from praatio import textgrid
from praatio.utilities.constants import Interval
from praatio.data_classes import interval_tier
from pathlib import Path

def get_textgrid_filenames(directory):
    p = Path(directory)
    return list(p.glob('*.TextGrid'))

def open_textgrid(filename):
    return textgrid.openTextgrid(filename,False)

def get_transcription(tg):
    entries = tg.getTier('ocr').entries
    if entries: return entries[0].label

def get_annotation(tg):
    entries = tg.getTier('alignment').entries
    if entries: return entries[0].label

def get_turn(filename, rttm):
    _, speaker, start_index = filename.stem.split('__')
    start_index = int(start_index)
    for turn in rttm.turns:
        if turn.speaker == speaker and turn.start_index == start_index:
            return turn

def handle_textgrid(filename, rttm):
    tg = open_textgrid(filename)
    transcription = get_transcription(tg)
    annotation = get_annotation(tg)
    turn = get_turn(filename,rttm)
    d = {'transcription': transcription, 'annotation': annotation, 'turn': turn,
        'filename': filename}
    return d

def handle_textgrids(directory, rttm):
    filenames = get_textgrid_filenames(directory)
    output = {}
    error = []
    for filename in filenames:
        d = handle_textgrid(filename, rttm)
        turn = d['turn']
        if not turn: error.append(filename)
        speaker = turn.speaker
        if speaker not in output.keys():
            output[speaker] = []
        output[speaker].append(d)
    return output, error
    
def turn_duration(turn):
    return sum([word.duration for word in turn.words])

def turn_duration_exclude(turn, exclude_words = ''):
    exclude_words = exclude_words.split(' ')
    nexclude = len(exclude_words)
    nwords = len(turn.words)
    d = [word.duration for word in turn.words if word.word not in exclude_words]
    if len(d) != nwords - nexclude:
        return sum(d), False
    return sum(d), True

def get_annotations(output, annotation_type = 'bad'):
    annotations = {}
    for speaker in output.keys():
        annotations[speaker] = {annotation_type:[],'other':[]}
        n = 0
        for d in output[speaker]:
            a = d['annotation']
            if not a: continue
            turn = d['turn']
            duration = turn_duration(turn)
            if annotation_type in a: 
                annotations[speaker][annotation_type].append(duration)
            else:
                annotations[speaker]['other'].append(duration)
    return annotations

def output_to_speaker_duration(output, speaker):
    turns = [x['turn'] for x in output[speaker] if x['turn']]
    duration = sum([turn_duration(turn) for turn in turns])
    return round(duration,2)


def show_annotations(output, annotation_type = 'bad', show_other = True):
    annotations = get_annotations(output, annotation_type)
    for speaker in annotations.keys():
        total = output_to_speaker_duration(output, speaker)
        at = annotations[speaker][annotation_type]
        other = annotations[speaker]['other']
        print(speaker.ljust(12), annotation_type.ljust(8), 
            str(len(at)).ljust(5), str(round(sum(at),2)).rjust(7),
            str(total).rjust(7), str(round(sum(at)/total*100,2)).rjust(6)+'%')
        if not show_other: continue
        print(speaker.ljust(12), 'other'.ljust(8), 
            str(len(other)).ljust(5), str(round(sum(other),2)).rjust(7))
        print('-')

def show_all_annotations(output):
    for annotation_type in ['ok','short','more','partial','bad','unk']:
        show_annotations(output, annotation_type, False)

def output_to_all_annotations(output, annotation_type = None):
    annotations = []
    for speaker in output.keys():
        for d in output[speaker]:
            if not d['annotation']:
                continue
            if annotation_type == None:
                annotation_type.append(d)
                continue
            elif annotation_type in d['annotation']:
                annotations.append(d)
    return annotations
    
def compute_ok_mismatch_time(output):
    ok = output_to_all_annotations(output, 'ok')
    annotations = [x['annotation'] for x in ok]
    durations = []
    for a in annotations:
        if ',' in a:
            duration = a.split(',')[1]
            try:duration = float(duration)
            except: continue
            else: durations.append(duration)
    total = sum([turn_duration(x['turn']) for x in ok])
    print('annotations:',len(annotations), 'durations:',len(durations))
    print('total duration:', round(total))
    print('total mismatch duration:', round(sum(durations)))
    print('average mismatch duration:', round(sum(durations)/len(durations),2))
    print('max mismatch duration:', round(max(durations),2))

    return durations
    

    

