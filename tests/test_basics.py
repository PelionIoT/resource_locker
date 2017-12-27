from tests.base import BaseCase

from resource_locker import RequirementNotMet

from resource_locker import Lock
from resource_locker import R
from resource_locker import P


class Test(BaseCase):
    def test_inits(self):
        a = Lock('a')
        r = a.requirements[0]
        self.assertEqual('a', r.get_potentials()[0].key)
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
            self.assertEqual(thing, r.get_potentials()[0].item)
            self.assertEqual('123', r.get_potentials()[0].key)

    def test_r_usage(self):
        r = R('a', 'b')
        # force fulfilment
        r.get_potentials()[0].fulfill()
        self.assertEqual(r.items[0].key, 'a')

    def test_reset(self):
        p = P('a')
        r = R(p)
        p.fulfill()
        r.validate()
        self.assertTrue(r.is_fulfilled)
        self.assertTrue(p.is_fulfilled)
        r.reset()
        self.assertFalse(r.is_fulfilled)
        self.assertFalse(p.is_fulfilled)

    def test_requirement(self):
        a = P('a')
        a.reject()
        b = P('b')
        b.reject()
        c = P('c')
        c.fulfill()

        with self.subTest(part='impossible'):
            with self.assertRaises(RequirementNotMet):
                R(a, b, c, need=5).validate()

        with self.subTest(part='not enough'):
            with self.assertRaises(RequirementNotMet):
                R(a, b, c, need=2).validate()

        with self.subTest(part='ok'):
            R(a, b, c, need=1).validate()
