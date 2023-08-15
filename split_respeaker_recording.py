import os

def split_audio(filename, ext = '.wav'):
    output_file = filename.replace('.w64','')
    for ch in range(1,7):
        cmd = 'sox ' + filename + ' ' + output_file
        cmd += '_ch-' + str(ch) + ext + ' remix ' + str(ch)
        os.system(cmd)

# sox respeaker_aug_ede_politie_lang.w64 respeaker_ch-1.wav remix 1
