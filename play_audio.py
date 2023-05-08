import pyaudio
import wave

def play(filename):
    wf = wave.open(filename,'rb')
    p = pyaudio.PyAudio()
    stream = _open_stream(wf, p)
    _play_stream(wf, stream)
    stream.stop_stream()
    stream.close()
    p.terminate()
    

def _open_stream(wf, p):
    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels = wf.getnchannels(),
        rate = wf.getframerate(),
        output = True)
    return stream

def _play_stream(wf, stream):
    data = wf.readframes(1014)
    while data:
        stream.write(data)
        data = wf.readframes(1024)
        
