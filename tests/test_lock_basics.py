from tests.base import BaseCase

from resource_locker import RequirementNotMet

from resource_locker import Lock
from resource_locker import R
from resource_locker import P
from resource_locker import NativeLockFactory


class Test(BaseCase):
    def test_inits(self):
        a = Lock('a')
        r = a._requirements[0]
        self.assertEqual('a', r.potentials[0].key)
        self.assertFalse(r.is_fulfilled)

    def test_invalid_inits(self):
        with self.subTest(part='same key'):
            with self.assertRaises(ValueError):
                Lock('a', 'b', R('b', 'c'))
        with self.subTest(part='invalid requirement'):
            with self.assertRaises(RequirementNotMet):
                Lock('a', need=2)

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
            self.assertEqual(thing, r.potentials[0].item)
            self.assertEqual('123', r.potentials[0].key)

    def test_sane_default(self):
        Lock()

    def test_release_failure(self):
        a = P('a')
        b = P('b')
        b.fulfill = None  # so that acquiring it fails

        lock = Lock(a, b, block=False, lock_factory=NativeLockFactory())
        lock._obtained.append('x')  # mess with internal state so that release also fails

        with self.assertRaises(TypeError):  # error comes from the fulfillment failure, not the release
            lock.acquire()

    def test_tags(self):
        p = P('a', tag_gen=lambda x: {'x': 1, 'y': 2})
        self.assertEqual(p.tags, dict(key='a', x=1, y=2))
