import unittest

from tests.base import BaseCase

from resource_locker import RequirementNotMet

from resource_locker import Lock
from resource_locker import R
from resource_locker import P

import threading
from functools import partial


def setUpModule():
    Lock().clear_all()


class Test(BaseCase):
    lock_class = Lock

    @classmethod
    def setUpClass(cls):
        cls.lock_class = partial(cls.lock_class, block=False)

    def test_lock_one(self):
        try:
            with self.assertRaises(RequirementNotMet):
                a = self.lock_class('a')
                a.clear_all()
                a.acquire()
                self.assertListEqual(['a'], a.get_lock_list())
                self.lock_class('a').acquire()
        finally:
            a.release()

    def test_lock_two(self):
        r1 = R('a', 'x', 'y', 'z')
        with self.lock_class(r1, 'b') as obtained:
            first = obtained[0][0]
            self.assertIn(first, ['a', 'x', 'y', 'z'])
            self.assertEqual('b', obtained[1][0])
            self.assertEqual(first, r1[0][0])
            self.assertEqual(first, r1.fulfilled[0].item)
            self.assertEqual(1, len(r1.fulfilled))
            self.assertEqual(4, len(r1.potentials))

    def test_not_too_greedy(self):
        a = P('a').reject()
        b = P('b').reject()
        c = P('c')
        d = P('d')
        with self.lock_class(R(a, b, c, d, need=1)):
            self.assertTrue(c.is_fulfilled or d.is_fulfilled)
            self.assertFalse(c.is_fulfilled and d.is_fulfilled)

    def test_concurrent(self):
        a_req = R('a', 'b', need=1)
        a = self.lock_class(a_req, auto_renewal=False)
        b_req = R('a', 'b', need=1)
        b = self.lock_class(b_req, auto_renewal=False)
        with a as obtained_a:
            with b as obtained_b:
                self.assertNotEqual(a_req.fulfilled[0].key, b_req.fulfilled[0].key)

    @unittest.skip('soon...')
    def test_high_contention(self):
        want = R(*[str(i) for i in range(10)])
        consumers = [Lock(want) for i in range(20)]

        for consumer in consumers:
            t = threading.Thread(target=consumer.acquire)
            t.daemon = True
            t.start()
