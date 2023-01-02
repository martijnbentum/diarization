import glob  
import re
import string

table_directory = '/Users/u050158/IFADV/TABLE/'
wav_directory = '/Users/u050158/IFADV/WAV/'
table_fn = glob.glob(table_directory + '*.Table')
wav_fn = glob.glob(wav_directory + '*.wav')
txt_directory = '/Users/u050158/IFADV/TXT/'


def open_table(f, clean = True, return_text = False, remove_empty_table_lines = False):
    '''open a table file.
    clean           the transcriptions are normalized if True
    return_text     only the transcriptions are returned
    '''
    with open(f) as fin:
        t = fin.read()
    t = replace_special_chars(t)
    table = [line.split('\t') for line in t.split('\n') if line]
    for line in table:
        for index in [0,3,5]:
            line[index] = float(line[index])
        line[4] = int(line[4])
    if clean: table = clean_table(table)
    if return_text: return table_to_text(table)
    if remove_empty_table_lines: table = remove_empty_transcription_lines(table)
    return table

def remove_empty_transcription_lines(table):
    output = []
    for line in table:
        if not line[2]: continue
        output.append(line)
    return output

def write_text_files():
    ''' write all IFADV transcriptions to text files with normalized texts.'''
    for f in table_fn:
        identifier = filename_to_identifier(f)
        text = open_table(f, return_text = True)
        with open( txt_directory + identifier + '.txt', 'w') as fout:
            fout.write('\n'.join(text))

def filename_to_identifier(filename):
    '''map wav or table filename to IFADV identifier.'''
    identifier = filename.split('/')[-1]
    identifier = identifier.split('.')[0]
    identifier = identifier.split('_')[0]
    return identifier

def identifiers_to_filenames_dict():
    '''create a dict mapping IFADV identifier to wav and table filename.'''
    d = {}
    for f in table_fn:
        identifier = filename_to_identifier(f)
        if identifier not in d.keys():
            d[identifier] = {'table':f}
    for f in wav_fn:
        identifier = filename_to_identifier(f)
        if identifier not in d.keys():
            d[identifier] = {'wav':f}
        else: d[identifier]['wav'] = f
    return d

def clean_text(t):
    '''map raw text to normalized text.'''
    t = replace_special_chars(t)
    t = fix_apastrophe(t)
    t = fix_star(t)
    t = fix_punctuation(t)
    t = remove_words(t)
    return t

def clean_table(table):
    '''normalize the transcriptions in the table.'''
    for line in table:
        text = line[2]
        line[2] = clean_text(text)
    return table

def table_to_text(table):
    ''' extract transcriptions from table.'''
    text = []
    for line in table:
        if line[1] == 'spreker1' or line[1] == 'spreker2':
            if not line[2]: continue
            text.append(line[2])
    return text

def all_table_to_all_text():
    '''loads all tables to a single list of sentences.'''
    texts = []
    for f in table_fn:
        table = open_table(f)
        text = table_to_text(table)
        texts.extend(text)
    return texts

def all_words():
    '''extracts all word tokens from IFADV.'''
    texts = all_table_to_all_text()
    texts = ' '.join(texts)
    return texts.split(' ')

def fix_apostrophe_dict():
    '''maps apostrophe words e.g. 't to full words -> het.'''
    d ={}
    d["'t"] = 'het'
    d["'n"] = 'een'
    d["d'r"] = 'der'
    d["zo'n"] = 'zo een'
    d["da's"] = 'dat is'
    d["z'n"] = 'zijn'
    d["m'n"] = 'mijn'
    d["'m"] = 'hem'
    d["'r"] = 'er'
    d["'s"] = 'is'
    d["'ns"] = 'eens'
    return d

def fix_apastrophe(t):
    '''map words as 't and 'n to het and een, remove apostrophe for plural s.'''
    words = t.split(' ')
    d = fix_apostrophe_dict()
    output = []
    for word in words:
        if word in d.keys():
            o = d[word]
        else: o = word
        output.append(o)
    output = ' '.join(output)
    return output.replace("'",'')

def fix_star(t):
    '''retains first part of a word before the *.
    for example grappi*a maps to grappi
    '''
    words = t.split(' ')
    output = []
    for word in words:
        if '*' in word:
            o = word.split('*')[0]
            if len(o) == 1: continue
        else: o = word
        output.append(o)
    return ' '.join(output)
            
def fix_punctuation(t):
    '''remove all punctuation from transcriptions.
    should be called after replace_special_chars 
    '''
    for p in string.punctuation:
        t = t.replace(p, ' ')
    t = re.sub('\s+',' ',t)
    return t.strip(' ')

def special_chars_dict():
    '''the set of special characters in IFADV corpus mapped to utf8.
    '''
    e_acute = u'é' 
    e_diaeresis = u'ë'
    e_hat = u'ê' 
    e_grave = u'è'
    c_cedilla = u'ç'
    i_diaeresis = u'ï'
    u_diaeresis = u'ü'
    a_grave = u'à'
    d = dict([
        ['\\i"',i_diaeresis],
        ['\\u"',u_diaeresis],
        [ '\\c,',c_cedilla],
        ['\\e^',e_hat],
        ['\\e`',e_grave],
        ['\\e"',e_diaeresis],
        ["\\e'",e_acute],
        ['\\a`',a_grave]])                                           
    return d

def replace_special_chars(t):
    '''replace all special chars in  string t.'''
    d = special_chars_dict()
    for k in d.keys():
        t = t.replace(k,d[k])
    return t

def remove_words(t, remove = None):
    if not remove:
        remove = ['gg','ggg','gggg','xx','xxx','xxxx','um','uhm','kch']
        remove += ['mm','mmm']
    words = t.split(' ')
    output = []
    for word in words:
        if word in remove: continue
        if len(word) == 1: continue 
        output.append(word)
    return ' '.join(output)



