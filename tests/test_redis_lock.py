from tests.base import BaseCase

import resource_locker
from resource_locker import RequirementNotMet


from resource_locker import Lock
from resource_locker import R
from resource_locker import P

from functools import partial


class Test(BaseCase):
    lock_class = Lock

    @classmethod
    def setUpClass(cls):
        cls.lock_class = partial(cls.lock_class, block=False)

    def test_mutex_blocks(self):
        resource_locker.core.factory.default_lock_factory.clear_all()
        try:
            with self.assertRaises(RequirementNotMet):
                a = self.lock_class('a')
                a.acquire()
                all_lock_keys = resource_locker.core.factory.default_lock_factory.get_lock_list()
                self.assertListEqual(['a'], all_lock_keys)
                self.lock_class('a').acquire()
        finally:
            a.release()

    def test_two_reqs(self):
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

    def test_non_mutex(self):
        a_req = R('a', 'b', need=1)
        a = self.lock_class(a_req, auto_renewal=False)
        b_req = R('a', 'b', need=1)
        b = self.lock_class(b_req, auto_renewal=False)
        with a:
            with b:
                self.assertNotEqual(a_req.fulfilled[0].key, b_req.fulfilled[0].key)
