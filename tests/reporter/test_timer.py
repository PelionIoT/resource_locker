from tests.reporter.base import BaseCase
from resource_locker.reporter import Timer


class Test(BaseCase):
    def test_context(self):
        with Timer() as t:
            pass
        self.assertGreaterEqual(t.duration, 0)

    def test_stop_start(self):
        t = Timer()
        t.start().start()
        duration = t.stop()
        t.stop()
        self.assertGreaterEqual(t.duration, 0)
        self.assertGreaterEqual(duration, t.duration)
