from tests.base import BaseCase
from operator import itemgetter
import time
import threading
import logging

from resource_locker import R
from resource_locker import RedisLockFactory

from resource_locker.reporter import Aspects
from resource_locker.reporter import Reporter
from resource_locker.reporter import Query

quiet_logger = logging.getLogger('test_contention')
quiet_logger.setLevel(logging.DEBUG)


class Test(BaseCase):
    factory_class = RedisLockFactory
    concurrency_delay = 0.5
    concurrency = 12
    need = 2
    available = 5

    def setUp(self):
        Reporter()._clear_all()

    def test_high_contention(self):
        logging.info('Testing contention using %s', self.factory)
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
        with self.subTest(part='sum of counters'):
            self.assertEqual(expected, total)

        q = Query()
        with self.subTest(part='reporting - keys'):
            tags = q.all_values('key')
            self.assertListEqual(sorted(resources.keys()), tags)

        with self.subTest(part='reporting - accuracy'):
            for k, (l, v) in resources.items():
                reported = q.aspect('key', k, Aspects.lock_acquire_count)
                logging.info('%s %s (%s reported) %s', k, v, reported, '✓' if v == reported else '✗')
                self.assertEqual(v, reported)


def consumer(go, lock_class, need, delay, resources):
    go.wait()
    available = resources.items()
    kwargs = dict(
        wait_exponential_max=None,
        wait_exponential_multiplier=None,
    )
    with lock_class(
        R(*available, need=need, key_gen=itemgetter(0)),
        logger=quiet_logger,
        block=True,
        reporter_class=Reporter,
        **kwargs,
    ) as obtained:
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
