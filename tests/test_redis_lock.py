from tests.base import BaseCase

from resource_locker import RequirementNotMet

from resource_locker import Lock
from resource_locker import R


def setUpModule():
    Lock.clear_all()


class Test(BaseCase):
    lock_class = Lock

    def test_lock_one(self):
        try:
            with self.assertRaises(RequirementNotMet):
                a = self.lock_class('a')
                a.acquire()
                self.lock_class('a').acquire()
        finally:
            a.release()

    def test_lock_two(self):
        with self.lock_class('a', 'b') as obtained:
            print(obtained)

    def test_concurrent(self):
        a_req = R('a', 'b', need=1)
        a = self.lock_class(a_req, auto_renewal=False)
        b_req = R('a', 'b', need=1)
        b = self.lock_class(b_req, auto_renewal=False)
        with a as obtained_a:
            with b as obtained_b:
                self.assertNotEqual(a_req.items[0].key, b_req.items[0].key)
