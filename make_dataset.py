from pathlib import Path
import handle_phrases as hp
import unicodedata
import json

def remove_diacritics(text):
    f = unicodedata.normalize('NFD', text)
    return ''.join(c for c in f if not unicodedata.combining(c))


def phrase_to_dataset_line(phrase):
    filename = Path(phrase.table.wav_filename).name
    text = remove_diacritics(phrase.text)
    d = {'sentence': text,'start_time':phrase.start_time,
        'end_time':phrase.end_time, 'filename':filename,
        'channel':phrase.channel, 'overlap':phrase.overlap,
        'speaker':phrase.speaker.id, 'duration':phrase.duration}
    return d

def phrases_to_dataset(phrases = None):
    if not phrases:
        t = hp.make_all_tables()
        phrases = []
        for table in t:
            phrases += table.phrases
    dataset = [phrase_to_dataset_line(phrase) for phrase in phrases]
    json.dump(dataset, open('../ifadv_phrases.json','w'))
    return dataset
