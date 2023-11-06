from queue import Queue
from threading import Lock, Event, Thread
from time import time, sleep
from os import path
from io import BytesIO
import wave
import pyttsx4
from .speech_proc import SpeechProcessor
from .play_rec_audio import PlayAudio

SOUNDS_DIR = path.join(path.dirname(__file__), 'sounds')
TONES_1_5 = path.join(SOUNDS_DIR, '1_5.wav')
TONES_5_1 = path.join(SOUNDS_DIR, '5_1.wav') 

class CoreUI():
    def __init__(self):
        """
        The primary UI class. Handles input collection queue, voice input, voice output generation, and audio playback.
        """
        self._input_q = Queue()                 # stores user input events
        
        self._speech_proc = SpeechProcessor()   # speech recognition - phrase listener and trasncriber
        self._listening = Event()               # keeps track of whether or not to capture and store voice input
        self._use_wakeword = Event()            # keeps track of whether or not to use and listen for wakeword
        self.wakewords = ["computer"]           # the word(s) used for wakeword system
        self.timeout = 5                        # number of seconds to wait, when not receiving voice input, before stopping listening

        self._audio_player = PlayAudio()        # for playing any program sounds
        
        self._tts_engine = pyttsx4.init()       # speech-generation/tts engine

        self._sound_lock = Lock()               # lock used to safely call sound related methods from different threads
    
    #---------
    # user-input collection

    def _store_input(self, type:str, data):
        """Store user input in the input queue. Must specify the type of input and pass in the input data.
        `type` must be a string with one of the following values:
        - `TEXT` - input came from text input (typed in)
        - `VOICE` - input came from vocal audio input
        - `BTN_SOFT` - input came from software (GUI) button press or other input element event
        - `BTN_HARD` - input came from hardware button press or other hardware event
        """
        if type in ("TEXT", "VOICE", "BTN_SOFT", "BTN_HARD"):
            self._input_q.put((type, data))

    def get_input(self) -> tuple|None:
        """Get the oldest user input entry in input queue. Returns a tuple containing input type and the input data.
        Is non-blocking, but will wait 1/100th of a second before returning with None if there is no input"""
        try:
            return self._input_q.get(block=False)
        except:
            return None

    #---------
    # speech recognition

    def _get_voice_input(self):
        target_time = time() + self.timeout                         # set target time to be self.timeout-seconds from now
        while self._listening.is_set():
            if time() >= target_time:                               # if current time is past target time, stop listening
                self.stop_listening()
                continue
            audio = self._speech_proc.get_phrase(no_wait=True)      # check for audio without waiting
            if not audio:                                           # if there's no audio currently available, 
                sleep(0.1)                                          # sleep for moment and continue to next cycle (bypass everything below)
                continue
            self._store_input("VOICE", audio)                       # store this input in the input queue
            target_time = time() + self.timeout                     # reset target time

    def _check_for_wakeword(self):
        while self._use_wakeword.is_set():
            audio = self._speech_proc.get_phrase(no_wait=True)      # check for audio without waiting
            if not audio:                                           # if there's no audio currently available, 
                sleep(0.1)                                          # sleep for moment and continue to next cycle (bypass everything below)
                continue
            if not self._listening.is_set():                        # if not already listening for phrases, then check input for wakeword
                text = self.transcribe_audio(audio, self.wakewords) # if wakeword(s) was provided, transcribe audio to see if it has wakeword
                if any(w for w in self.wakewords if w in text):     # if the wakeword was in the phrase,                                                      
                    self.start_listening()                          # show UI notifications
                    self._store_input("VOICE", audio)               # store initial audio in input queue
                    self._get_voice_input()                         # run method to get voice input (will run in a loop until self._listening is False)

    def start_wakeword_detection(self):
        self._use_wakeword.set()
        self._speech_proc.start_stream()
        Thread(target=self._check_for_wakeword, daemon=True).start()

    def stop_wakeword_detection(self):
        self._use_wakeword.clear()
        self._speech_proc.stop_stream()

    def start_listening(self):
        """Start listening for voice input phrases"""
        self._listening.set()
        self.prog_sound("LISTENING")
        
        if not self._use_wakeword.is_set():
            self._speech_proc.start_stream()
            Thread(target=self._get_voice_input, daemon=True).start()

    def stop_listening(self):
        """Stop listening for voice input phrases"""
        self._listening.clear()
        self.prog_sound("DONE")

        if not self._use_wakeword.is_set():
            self._speech_proc.stop_stream()

    def transcribe_audio(self, audio:bytes, vocab:list=None) -> str:
        """Transcribe phrase audio data into text.
        `vocabulary` must be a list of words.
        If vocabulary is not provided, then the transcriber will use entire language vocabulary, which will take longer"""
        vocab = " ".join(vocab) if vocab else None                  # vocab list must be joined into a single string of words sperated by whitespace
        return self._speech_proc.transcribe(audio, vocab)

    #---------

    # program notification sounds
    def prog_sound(self, sound:str, wait:bool=True):
        """play program sound according to the `sound` string arg. 
        `wait` specifies if program will block until the audio is done playing - defualt is `True`."""
        sound_map = {
            "LISTENING":    TONES_1_5,
            "DONE":         TONES_5_1 
        }

        audio_path = sound_map.get(sound)

        if audio_path:
            with self._sound_lock:
                self._audio_player.play(audio_path, wait)

    # speech generation & output
    def say(self, message:str, wpm:int=200, wait:bool=False):
        """Play back audio of a computer generated voice saying a given string message in a sperate thread (non-blocking).
        However, if `wait` is set to `True`, this will block until the audio is done playing - defualt is `False`.
        `wpm` is an optional argument for speaking speed (words per minute). Default value is `200`."""
        self._audio_player.stop()                                   # stop any existing audio
        tts_file = BytesIO()                                        # temp file to store tts audio
        message = message.replace('\n', '')                         # remove any new-line characters
        self._tts_engine.setProperty('rate', wpm)                   # sets speaking rate in wpm (default is 200)
        self._tts_engine.save_to_file(message, tts_file)            # create tts audio file from message
        self._tts_engine.runAndWait()
        data = tts_file.getvalue()
        tts_file.seek(0)
        with wave.open(tts_file, 'wb') as f:                        # add wav header
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(22050)
            f.writeframes(data)
        tts_file.seek(0)

        with self._sound_lock:
            self._audio_player.play(tts_file, wait)                 # play tts audio file

    def is_making_sound(self) -> bool:
        """return `True` if UI is making sound, `False` if not"""
        if self._audio_player.get_state() == "OA":
            return True
        else:
            False

    def is_listening(self) -> bool:
        """return `True` if UI is listening for voice, `False` if not"""
        return self._listening.is_set()

    #def pause_resume_audio(self):
    #    pass

    def silence(self):
        """Stop any currently playing program audio"""
        self._audio_player.stop()
