import time


class Timer:
    def __init__(self):
        self._start = None
        self._duration = None

    def start(self):
        self._start = time.time()
        return self

    def stop(self):
        self._duration = time.time() - self._start if self.duration is None else self._duration
        return self.duration

    @property
    def duration(self):
        return self._duration

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()