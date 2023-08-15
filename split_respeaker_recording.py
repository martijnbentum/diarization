import glob
import os

def split_respeaker_audio(filename, ext = '.wav'):
    output_file = filename.replace('.w64','')
    for ch in range(1,7):
        cmd = 'sox ' + filename + ' ' + output_file
        cmd += '_ch-' + str(ch) + ext + ' remix ' + str(ch)
        os.system(cmd)

# sox respeaker_aug_ede_politie_lang.w64 respeaker_ch-1.wav remix 1
def split_grensvlak_audio():
    filename = '/Volumes/INTENSO/grensvlak_11-08-23/T71_ISO.wav'
    output_file = filename.replace('.wav','')
    print(os.path.isfile(filename),filename)
    for ch in range(1,4):
        cmd = 'sox ' + filename + ' ' + output_file
        cmd += '_ch-' + str(ch) + '.wav' + ' remix ' + str(ch)
        print(cmd)
        os.system(cmd)
        
