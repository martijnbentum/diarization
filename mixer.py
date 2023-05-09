import handle_phrases as ph
import ifadv_clean as ic

def concatenate_audio_files(filenames, silences, output_filename = 'default.wav'):
    assert len(filenames) == len(silences)
    cmd = 'sox --combine sequence '
    for filename, silence in zip(filenames, silences):
        pad = ' -p pad 0 ' + str(silence) 
        cmd += '"|sox ' + filename + pad + '" '
    cmd += '-b 16 ' + output_filename 
    return cmd
        




