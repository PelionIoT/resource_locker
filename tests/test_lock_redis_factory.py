from tests.base import BaseCase

from resource_locker import RedisLockFactory
from resource_locker import RequirementNotMet


from resource_locker import Lock
from resource_locker import R
from resource_locker import P


class Test(BaseCase):
    lock_class = Lock
    factory_class = RedisLockFactory

    def test_mutex_blocks(self):
        self.factory.clear_all()
        try:
            with self.assertRaises(RequirementNotMet):
                a = self.lock_class('a')
                a.acquire()
                all_lock_keys = self.factory.get_lock_list()
                self.assertIn('a', all_lock_keys)
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

    def test_already_fulfilled(self):
        a = P('a').reject()
        b = P('b').fulfill()
        c = P('c')
        l = self.lock_class(R(a, b, c, need=2))
        l._acquire_one(a)
        l._acquire_one(b)
        self.assertTrue(a.is_rejected)
        self.assertTrue(b.is_fulfilled)

    def test_non_mutex(self):
        a_req = R('a', 'b', need=1)
        a = self.lock_class(a_req, auto_renewal=False)
        b_req = R('a', 'b', need=1)
        b = self.lock_class(b_req, auto_renewal=False)
        with a:
            with b:
                self.assertNotEqual(a_req.fulfilled[0].key, b_req.fulfilled[0].key)

    def test_timeout(self):
        # sub-locks will block and then timeout if requested. unfortunately, 1s is the smallest valid value.
        with self.lock_class('a'):
            b = self.lock_class('a', timeout=1)
            with self.assertRaises(RequirementNotMet):
                b.acquire()
