import sys
from os.path import dirname, join
#sys.path.append(dirname(__file__))
from threading import Event
from io import BytesIO
from pyaudio import PyAudio, paInt16
import pyttsx4
from ._timer_class import SimpleTimer

def _generate_alarm_audio_file(message:str=None):
    DEFAULT_SOUND = join(dirname(__file__), "tone_on_off_3s.raw")   # 3 seconds of on/off beeps (0.5 sec of tone, 0.5 sec of silence per second)
    SAMPLE_RATE = 22050
    SAMPLE_WIDTH = 2
    b_file = BytesIO()

    with open(DEFAULT_SOUND, 'rb') as s:
        data = s.read()                         # get audio data from DEFAULT_SOUND
    if message:                                 # if message was provided, add tts audio of the message to data
        engine = pyttsx4.init()
        engine.save_to_file(message, b_file)
        engine.runAndWait()
        data += b_file.getvalue()
    else:                                       # if no message was provided, then just add 1 second of silence
        data += bytes([0]* (SAMPLE_RATE * SAMPLE_WIDTH))

    b_file = BytesIO(data)
    b_file.seek(0)

    return b_file

def _generate_timer_func(message:str=None):
    pa = PyAudio()
    alarm_file = _generate_alarm_audio_file(message)
    NBYTES = len(alarm_file.getbuffer())
    BUFFER = 1024 * 2
    
    stream = pa.open(
        format = paInt16,   # aka: sample width
        channels = 1,
        rate = 22050,
        output = True,
        )

    def func(flag:Event):
        while not flag.is_set():
            stream_pos = alarm_file.tell()
            if (stream_pos + BUFFER) > NBYTES:                  # if the number of bytes to read is more than what is left in the file,
                n_last_samps = NBYTES - stream_pos
                data = alarm_file.read1(n_last_samps)           # read only the remaining samples
                alarm_file.seek(0)
                data += alarm_file.read1(BUFFER - n_last_samps) # and then read BUFFER-number of samples minus the number of reamining samples
            else:
                data = alarm_file.read1(BUFFER)
            stream.write(data)
        stream.close()

    return func

#---------

_timers = []

_UNITS = {
    's':        1,
    'second':   1,
    'seconds':  1,
    'm':        60,
    'minute':   60,
    'minutes':  60,
    'h':        3600,
    'hour':     3600,
    'hours':    3600
}

def _convert_time_to_seconds(quantity:int|float, unit:str) -> int:
    if not unit in _UNITS:
        raise ValueError()
    return quantity * _UNITS.get(unit)

def _convert_seconds_to_time_str(seconds:int) -> str:
    h = int(seconds / 3600)
    m = int(seconds % 3600 / 60)
    s = int(seconds % 3600 % 60)
    h = f"{h} hours " if h > 1 else f"{h} hour "
    m = f"{m} minutes " if m > 1 else f"{m} minute "
    s = f"{s} seconds" if s > 1 else f"{s} second"
    if seconds >= 3600:
        return h + m + s
    elif seconds >= 60:
        return m + s
    else:
        return s

def _get_timer(ordinance:int=None, seconds:int=None, message:str=None) -> tuple|None:
    timer = None
    if ordinance and ordinance <= len(_timers):
        timer = _timers[ordinance]      # return the timer at the index, provided by `ordanance`
    elif seconds:
        for n, secs, mes, tim in enumerate(_timers):
            if secs == seconds:
                timer = _timers[n]      # if `seconds` was provided, return the first created timer whose seconds value matches `seconds`
    elif message and _timers:
        pass
        # get timer with closest message match
    elif _timers:
        timer = _timers[-1]             # if neither `ordinance` nor `message` was given (and timers not empty), return the last created timer
    
    return timer

#---------

def start_new_timer(seconds:int, message:str=None, func=None):
    """Create a new timer and start it"""
    func = func if func else _generate_timer_func(message)
    _timers.append((seconds, message, SimpleTimer(seconds, func, pass_flag=True)))
    return _convert_seconds_to_time_str(seconds)

def stop_timer(ordinance:int=None, seconds:int=None, message:str=None):
    """Stop a timer whose time is up, or cancel a timer that's still running."""
    timer = None
    for t in _timers:
        if t[2].get_time_left() <= 0:
            timer = t                                   # firstly, check for the earliest made timer (if any) that has no more time left
            break
    if not timer:
        timer = _get_timer(ordinance, seconds, message) # if all timers are still active, then check get a timer based on ordinance, seconds, or message
    if timer:
        _timers.remove(timer)
        timer[2].stop()                                 # if a timer was returned, then remove it from the list and stop it

def get_remaining_time(ordinance:int=None, seconds:int=None, message:str=None):
    """Get the remaining time on a timer"""
    timer = _get_timer(ordinance, seconds, message)
    if timer:
        return _convert_seconds_to_time_str(timer[2].get_time_left())

def is_any_timers():
    """return whether or not there are any timers active"""
    return True if _timers else False