import ifadv_clean

class Table:
    def __init__(self,table_filename):
        self.table_filename = table_filename
        self.table = ifadv_clean.open_table(table_filename, 
            remove_empty_table_lines = True)
        self.wav_filename = table_to_wav_filename(self.table_filename)

class Phrase:
    def __init__(self,table, phrase_index):
        self.phrase = table[phrase_index]
        self.table = table
        self.phrase_index = phrase_index


def table_to_wav_filename(table_filename):
    f = table_filename.split('/')[-1].split('_')[0]
    return ifadv_clean.wav_directory + f + '.wav'
