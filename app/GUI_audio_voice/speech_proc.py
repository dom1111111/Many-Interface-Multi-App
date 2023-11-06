from os import path
import json
import numpy as np
from queue import Queue
from vosk import Model, KaldiRecognizer, SetLogLevel
from faster_whisper import WhisperModel
from .play_rec_audio import RecAudio

#-------------

class _WhisperT:
    def __init__(self):
        model_path = "tiny.en"                                  # choice between "tiny", "base", "small", "medium", "large"
        self.model = WhisperModel(model_path)
        self.no_speech_prob_threshold = 0.1                     # the lower the float, the more strict the transcription wuality filtering will be

    def transcribe(self, audio_data):
        """transcribe!"""
        audio_data = np.frombuffer(audio_data, np.int16).flatten().astype(np.float32) / 32768.0     # convert audio data into format that transcriber can use
        segments, info = self.model.transcribe(audio_data, language="en")                           # trasncribe audio
        text = ""
        for seg in segments:                                    # combine the text of each segment together, so long as its no-speech-probability is below the threshhold
            seg = seg._asdict()
            if seg['no_speech_prob'] < self.no_speech_prob_threshold:
                text += seg['text'].strip() + " "
        return text.strip()

class _VoskT:
    def __init__(self):
        model_path = path.join(path.dirname(__file__), "vosk_models", "vosk-model-small-en-us-0.15")
        SetLogLevel(-1)                                         # disables kaldi output messages
        self.model = Model(model_path = model_path, lang='en-us')
        self.reset()

    def reset(self):
        """Reset transcriber back to using full vocabulary, and reset word times for transcription"""
        self.recognizer = KaldiRecognizer(self.model, 16000)    # spawn a new recognizer to reset vocabulary  
        self.recognizer.SetWords(True)                          # set this to true to have results come with time and confidence

    def transcribe(self, audio_data, words_to_recognize:str=None, get_metadata:bool=False) -> str|tuple[str,dict]:
        """`words_to_recognize` must be a single string, with the words separated by whitespace"""
        # transcribe audio
        if words_to_recognize:
            words = f'["{words_to_recognize}", "[unk]"]'
            self.recognizer.SetGrammar(words)
        self.recognizer.AcceptWaveform(audio_data)
        json_result = self.recognizer.Result()
        # extract text of transcription
        dict_result = json.loads(json_result)
        text = dict_result.get('text')
        text = text.replace('[unk]', '')                        # this makes sure to remove "[unk]" from text
        text = text.strip()

        if get_metadata:
            return text, dict_result
        return text

#-------------
# main classes

class SpeechProcessor:
    def __init__(self):
        """The class for capturing voice phrases and transcribing them into text"""
        #-- Audio Recorder and Audio Paramters --#
        self._rec = RecAudio()
        self._sample_rate = 16000
        self._sample_width = 16
        self._n_channels = 1
        self._chunks_per_second = 5
        self._chunk = round(self._sample_rate/self._chunks_per_second)
        self._rec.set_pars(self._chunk, self._n_channels, self._sample_rate)    # set the recorder's audio parameters
        #-- Phrase Detection --#
        self._audio_threshold = 675                             # value from 0-65535 (65535 is the max possible value for int16 array (unbalanced) of audio data) 
        self._minimum_phrase_length = 0.3                       # in seconds
        self._phrase_chunks = []                                # holds the recorded audio data chunks which are above the threshold
        self._audio_q = Queue()                                 # holds audio data for phrases, ready for transcription
        #-- Transcribers --#
        self._limited_vocab_transcriber = _VoskT()              # the limited vobcabulary transcriber
        self._full_vocab_transcriber = _WhisperT()              # the full vocabulary transcriber

    #----- Phrase Capture Support Methods -----#

    def __get_audio_power(self, data):
        data_array = np.frombuffer(data, dtype="int16")
        sample_value_range = abs(int(np.max(data_array)) - int(np.min(data_array)))
        # mean_sample_value = mean(abs(audio_data_array))
        return sample_value_range

    def __detect_phrase(self, chunk:bytes):
        audio_power = self.__get_audio_power(chunk)
        minimum_chunks = round(self._minimum_phrase_length * self._chunks_per_second)

        if audio_power > self._audio_threshold:
            self._phrase_chunks.append(chunk)
        
        elif audio_power < self._audio_threshold and self._phrase_chunks:
            if len(self._phrase_chunks) >= minimum_chunks:
                self._phrase_chunks.append(chunk)
                phrase_audio_data = b''.join(self._phrase_chunks)
                # put audio into queue
                self._audio_q.put(phrase_audio_data)

            # regardless of above condition, clear phrase_chunks
            self._phrase_chunks.clear()

    #----- Phrase Capture Accessbile Methods -----#

    def start_stream(self):
        """start listening for voice input"""
        self._rec.set_callback(self.__detect_phrase)            # set recording callback to `__detect_phrase` function
        self._rec.record()                                      # start recording!

    def is_stream_active(self):
        """return `True` if currently listening for voice input, otherwise return `False`"""
        state = self._rec.get_state()
        if state == "OA":
            return True
        else:
            return False

    def stop_stream(self):
        """stop listening for voice input"""
        self._rec.stop()

    #----- Phrase Getting and Editing Methods -----#    

    def get_phrase(self, no_wait:bool=False) -> bytes:
        """Get the oldest phrase in the queue"""
        try:
            return self._audio_q.get(block=not no_wait)
        except:
            return

    def get_phrase_length(self, phrase:bytes) -> float:
        """Get the length of a phrase in seconds"""
        n_bytes_per_sample = self._sample_width / 8
        return len(phrase) / self._sample_rate / n_bytes_per_sample
    
    # def remove_words_from_phrase(self, phrase:bytes, transcription_data:dict) -> bytes:
    #     """Remove all audio corresponding to the containing the words from phrase"""
    #     phrase_len = self.get_phrase_length(phrase)
    #     min_word_time = transcription_data['result'][0]["start"]
    #     max_word_time = transcription_data['result'][-1]["end"]
    #     return
    
    #----- Phrase Transcription Methods -----#

    def transcribe(self, audio_data:bytes, vocabulary:str='') -> str:
        """Transcribe phrase audio data into text.
        `vocabulary` must be a single string, with the words separated by whitespace.
        If vocabulary is not provided, then the transcriber will use entire language vocabulary, which will take longer"""
        if vocabulary:
            return self._limited_vocab_transcriber.transcribe(audio_data, vocabulary)
        return self._full_vocab_transcriber.transcribe(audio_data)
