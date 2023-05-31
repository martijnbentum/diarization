import os
from wonderwords import RandomWord
r = RandomWord()

def random_word():
    word = r.word(include_parts_of_speech=['noun','adjectives'],
        word_max_length=8)
    return word

def random_words(n):
    words = [random_word() for _ in range(n)]
    return words

def say_random_word():
    word = random_word()
    say(word)

def say_random_words(n):
    words = ' '.join(random_words(n))
    say(words)

def say(text):
    cmd = 'say -v Moira ' + text
    print(cmd)
    os.system(cmd)

def record_random_word(say_word = True):
    word = random_word()
    output_filename = word
    record(word, output_filename)
    if say_word: say(word)

def record_random_words(n, say_words = True):
    words = '_'.join(random_words(n))
    output_filename = words
    record(words, output_filename)
    if say_words: say(words)

def record(text, output_filename):
    if '.' in output_filename:
        raise ValueError(output_filename,'should not contain extension')
    cmd = 'say -v Moira ' + text + ' -o ' + output_filename + '.aiff'
    os.system(cmd)
    print(cmd)
    sox_cmd = 'sox ' + output_filename + '.aiff ' + output_filename + '.wav'
    os.system(sox_cmd)
    os.system('rm ' + output_filename + '.aiff')
