import glob
import os
import locations

def split_all_respeakers_audio():
    split_respeaker_audio(locations.respeaker_left_filename)
    split_respeaker_audio(locations.respeaker_right_filename)

def split_respeaker_audio(filename, ext = '.wav'):
    output_file = filename.replace('.w64','')
    for ch in range(1,7):
        cmd = 'sox ' + filename + ' ' + output_file
        cmd += '_ch-' + str(ch) + ext + ' remix ' + str(ch)
        os.system(cmd)

# sox respeaker_aug_ede_politie_lang.w64 respeaker_ch-1.wav remix 1
def split_grensvlak_audio():
    filename = locations.grensvlak_filename
    output_file = filename.replace('.wav','')
    print(os.path.isfile(filename),filename)
    for ch in range(1,4):
        cmd = 'sox ' + filename + ' ' + output_file
        cmd += '_ch-' + str(ch) + '.w64' + ' remix ' + str(ch)
        print(cmd)
        os.system(cmd)
        
