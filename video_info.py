import glob
import locations
import os
import subprocess

def _make_video_info(output_name, video_dir= locations.video_directory, 
    ext = '.avi'):
    '''create information text for video files in a given directory.'''
    fn = glob.glob(video_dir + '*' + ext)
    output = []
    for f in fn:
        file_id = f.split('/')[-1].split('.')[0]
        o = subprocess.check_output('ffmpeg -i ' + f, shell =True)
        o = o.decode().replace('\n','\t').strip()
        o = o.replace('\t',',').replace("'",'')
        o = re.sub('\s+','',o)
        output.append(file_id + '\t' + o)
    with open(locations.video_info+output_name,'w') as fout:
        fout.write('\n'.join(output))
    return output


def make_video_info_json(video_dir = locations.video_directory, ext = '.avi'):
    '''create information text for video files in a given directory.'''
    fn = glob.glob(video_dir + '*' + ext)
    directory = locations.video_info 
    for f in fn:
        file_id = f.split('/')[-1].split('.')[0]
        print(file_id)
        cmd = 'ffprobe -v quiet -print_format json -show_format '
        cmd += '-show_streams ' + f + ' > ' + directory + file_id +'.json'
        print(cmd)
        os.system(cmd)

