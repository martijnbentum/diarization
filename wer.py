import glob
import ifadv_clean
import jiwer

base_w2v_directory = '/Users/u050158/IFADV/wav2vec2_transcriptions/'

fn_base_w2v_transcriptions = glob.glob(base_w2v_directory + '*.txt')


def table_filename_to_w2v_filename(table_filename, 
    fn_w2v=fn_base_w2v_transcriptions):
    table_id = ifadv_clean.filename_to_identifier(table_filename)
    for f in fn_w2v:
        w2v_id = ifadv_clean.filename_to_identifier(f)
        if table_id == w2v_id: return f
    return None

def open_wav2vec(filename):
    with open(filename) as fin:
        t = fin.read()
    return t

def compute_wer_base_wav2vec(verbose = True):
    table_fn = ifadv_clean.table_fn
    d = {}
    for f in table_fn:
        wav2vec_filename = table_filename_to_w2v_filename(f)
        wav2vec = open_wav2vec(wav2vec_filename)
        manual = ifadv_clean.open_table(f,return_text = True)
        manual = ' '.join(manual).lower()
        identifier = ifadv_clean.filename_to_identifier(f)
        wer = jiwer.wer(manual, wav2vec)
        d[identifier] = {}
        d[identifier]['manual'] = manual
        d[identifier]['wav2vec'] = wav2vec
        d[identifier]['manual300'] = manual[:300]
        d[identifier]['wav2vec300'] = wav2vec[:300]
        d[identifier]['wer'] = wer
        d[identifier]['filename_wav2vec'] = wav2vec_filename
        d[identifier]['filename_table'] = f
        if verbose: print(identifier, wer)
    return d

