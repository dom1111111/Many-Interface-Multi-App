from threading import Thread, Event
from time import time, sleep


class SimpleTimer:
    def __init__(self, seconds:int, func, pass_flag:bool=False):
        """Start a timer for a specified number of seconds. Once the timer is compelte, 
        the provided in function will be called. If `pass_flag` is True, 
        then the `self._complete` Event will be passed in as the first argument.
        This can be used as a mechanism to end and return the function when `stop()` is called.
        If stop() is called prior to the timer being complete, the timer will be cancelled"""
        self._target = time() + float(seconds)
        self._complete = Event()
        self._pass_flag = pass_flag
        Thread(target=self._waiter, args=(seconds, func), daemon=True).start()

    def _waiter(self, seconds:int, func):
        self._complete.wait(seconds)                # wait for the time left or until complete is True
        if time() >= self._target:                  # if the current time has passed the target, then perform the alarm function
            if self._pass_flag:
                func(self._complete)
            else:
                func()

    def stop(self):
        """cancels timer if it still has time left, otherwise stops timer function if not"""
        self._complete.set()

    def get_time_left(self) -> int:
        """return the current number of seconds left in the timer"""
        return self._target - time()


class Timer:
    def __init__(self, seconds:int):
        """start a timer for a specified number of seconds"""
        self._inactive = Event()
        self.complete = Event()
        self._time_left = seconds
        self._target = time() + self._time_left
        self.start()

    def _waiter(self):
        self._inactive.wait(self._time_left)            # wait for the time left or until inactive is True
        if time() >= self._target:                      # if the current time has passed the target, then set complete
            self.complete.set()

    def start(self):
        """starts or resumes paused timer"""
        if self._inactive.is_set():
            self._target = time() + self._time_left
            self._inactive.clear()
            Thread(target=self._waiter, daemon=True).start()

    def stop(self):
        """pauses timer if it still has time left, otherwise stops alarm sound if done"""
        if not self._inactive.is_set():
            self._time_left = self._target - time()
            self._inactive.set()

    def get_time_left(self) -> int:
        """return the current number of seconds left in the timer"""
        if self._inactive.is_set():
            return self._time_left
        else:
            return self._target - time()


class AltTimer:
    def __init__(self, seconds:int):
        """start a timer for specified number of seconds"""
        self._seconds = seconds
        self._active = Event()
        Thread(target=self._timer, daemon=True).start()

    def _timer(self):
        self._active.set()          # set active flag to True
        while self._seconds > 0:    # while there are more than 0 seconds left
            self._active.wait()     # wait for self.active to be True
            sleep(1)
            self._seconds -= 1      # sleep for 1 second, then subtract 1 from self.seconds
        print('timer complete!')
        while self._active.is_set():
            pass
            sleep(0.5)
            # play sound in loop until stop() is called

    def resume(self):
        """resumes paused timer"""
        self._active.set()

    def stop(self):
        """pause timer if it still has time left, otherwise stops alarm sound if done"""
        self._active.clear()
    
    def get_seconds_left(self) -> int:
        """return the current number of seconds left in the timer"""
        return self._seconds
