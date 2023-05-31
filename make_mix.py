import glob
import handle_phrases 
import mixer

mixed_audio = '/Users/u050158/mixed_audio/'
tone_audio = '/Users/u050158/tone_mixed_audio/'

def make_all_mixes(tables = None):
    if not tables: tables = handle_phrases.Tables()
    make(tables = tables, tids = ['DVA1A','DVA2C','DVA24AK'])
    make(tables = tables, tids = ['DVA1A','DVA24AK'])
    make(tables = tables, tids = ['DVA1A'])
    make(tables = tables, tids = ['DVA2C'])
    make(tables = tables, tids = ['DVA24AK'])


def make(tables = None, tids = ['DVA1A','DVA2C','DVA24AK']):
    if not tables: tables = handle_phrases.Tables()
    ta, turns = tables.select_tables(tids)
    _make(turns, overlap = False)
    _make(turns, overlap = True)


def _make(turns, overlap):
    tracks = mixer.Tracks(turns, overlap = overlap)
    tracks.make()

def add_start_tone_to_audio_files(input_dir=mixed_audio,output_dir=tone_audio):
    fn = glob.glob(input_dir + '*.wav')
    for f in fn:
        output_filename = output_dir + 'tone_' + f.split('/')[-1]
        print(f, output_filename)
        mixer.add_start_tone(f, output_filename)
    

    

