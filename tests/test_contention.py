from tests.base import BaseCase
from operator import itemgetter
import time
import threading
import logging

from resource_locker import Lock
from resource_locker import R


class Test(BaseCase):
    concurrency_delay = 0.5
    lock_class = Lock
    concurrency = 20
    need = 2
    available = 5

    def test_high_contention(self):
        resources = {f'contention-{i+1}': [threading.Lock(), 0] for i in range(self.available)}
        consumers = []

        go = threading.Event()
        for i in range(self.concurrency):
            t = threading.Thread(target=consumer, kwargs=dict(
                lock_class=self.lock_class,
                resources=resources,
                need=self.need,
                go=go,
                delay=self.concurrency_delay,
            ))
            t.daemon = True
            t.start()
            consumers.append(t)

        go.set()
        [t.join() for t in consumers]

        # we should have a total of need * concurrency across all the counters
        expected = self.concurrency * self.need
        total = 0
        for k, (l, v) in resources.items():
            # grab internal state
            total += v
            logging.info('%s %s', k, v)
        logging.info('total %s / %s', total, expected)
        self.assertEqual(expected, total)


def consumer(go, lock_class, need, delay, resources):
    go.wait()
    available = resources.items()
    kwargs = dict(
        wait_exponential_max=None,
        wait_exponential_multiplier=None,
    )
    with lock_class(R(*available, need=need, key_gen=itemgetter(0)), **kwargs) as obtained:
        for resource in obtained[0]:  # in the first Requirement
            # we passed in a list of tuples [(key, (lock, counter))]
            have_lock = resource[1][0].acquire(blocking=False)
            if have_lock:
                # increment the counter and release
                if delay:
                    time.sleep(delay)
                resource[1][1] += 1
                resource[1][0].release()
            else:
                raise ValueError('cross-check lock was in use')
