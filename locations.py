# base ='/Volumes/INTENSO/diarization_10-08-23/third_session_play/'
base = '/Volumes/BACKUP_4TB/diarization_30-08-23/'

base_play = base + 'third_session_play/'
base_support = base + 'SUPPORT/'

#played audio and supporting files
section_directory = base_play + 'third_recording_session/' 
combined_directory = base_play + 'third_recording_session_combined/'
mono_directory = base_play + 'third_recording_session_mono/'
tone_directory = base_play + 'third_recording_session_tone/'
original_directory = base_play + 'original/'
original_tone_directory = base_play + 'original_tone/'
original_combined_directory= base_play + 'original_combined/'

#support
audio_id_directory = base_support+ 'AUDIO_ID/'
random_word_directory = base_support + 'RANDOM_WORDS/'
play_transcription_tables_directory = base_support
play_transcription_tables_directory += 'PLAY_TRANSCRIPTION_TABLES/'
play_textgrids_directory = base_support
play_textgrids_directory += 'PLAY_TEXTGRIDS/'
audio_info = base_support + 'audio_info/'
recording_name_channels_filename=base_support+'recording_name_channels.txt'
support_tones_directory = base_support + 'TONE/'
recording_data_filename = base_support + 'recording_data.txt'
speaker_data_filename = base_support + 'speaker_data.txt'
#audio id to section mappers
audio_id_filename =base_support + 'mix_id_to_audio_id_mapping.txt'
audio_id_original_filename=base_support +'audio_id_mapping_orginal_ifadv.txt'

#recorded audio
base_rec = base
grensvlak_directory = base_rec + 'grensvlak/'
minidsp_directory = base_rec + 'minidsp/'
shure_directory = base_rec + 'shure_mxa910/'
left_respeaker_directory = base_rec + 'respeaker_links/'
right_respeaker_directory = base_rec + 'respeaker_rechts/'


#split audio files
grensvlak_filename = base_rec + 'grensvlak/T72_ISO.wav'
respeaker_left_filename = left_respeaker_directory 
respeaker_left_filename += 'respeaker_politie_30-8-23.w64'
respeaker_right_filename = right_respeaker_directory 
respeaker_right_filename += 'respeaker_spraakdetector_30-8-23.wav'

# ifadv
ifadv_dir = base_play + 'IFADV/'
ifadv_table_directory =ifadv_dir + 'TABLE/'
ifadv_wav_directory = ifadv_dir + 'WAV/'
ifadv_txt_directory = ifadv_dir +'/TXT/'
