from tests.base import BaseCase

from resource_locker import Lock
from resource_locker import R
from resource_locker import P


def setUpModule():
    Lock.clear_all()


class TestSomething(BaseCase):
    def test_inits(self):
        a = Lock('a')
        r = a.requirements[0]
        self.assertEqual('a', r.get_potentials()[0].key)
        self.assertFalse(r.is_fulfilled)

    def test_invalid_inits(self):
        with self.subTest(invalid='same key'):
            with self.assertRaises(ValueError):
                Lock('a', 'b', R('b', 'c'))

    def test_key_gen(self):
        def dict_str_id(d):
            return str(d['id'])
        thing = dict(id=123, x='y')

        with self.subTest(part='direct'):
            p = P(thing, key_gen=dict_str_id)
            self.assertEqual(thing, p.item)
            self.assertEqual('123', p.key)

        with self.subTest(part='via R'):
            r = R(thing, key_gen=dict_str_id)
            self.assertEqual(thing, r.get_potentials()[0].item)
            self.assertEqual('123', r.get_potentials()[0].key)

    def test_lock_one(self):
        with Lock('a', 'b') as obtained:
            print(obtained)

    def test_lock_two(self):
        try:
            with self.assertRaises(Exception):
                a = Lock('a')
                a.acquire()
                Lock('a', timeout=1).acquire()
        finally:
            a.release()
