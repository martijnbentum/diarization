import handle_phrases 
import mixer

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

