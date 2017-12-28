from tests.base import BaseCase

from resource_locker import RequirementNotMet

from resource_locker import Lock
from resource_locker import R
from resource_locker import P


class Test(BaseCase):
    def test_inits(self):
        a = Lock('a')
        r = a.requirements[0]
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

    def test_r_usage(self):
        r = R('a', 'b')
        # force fulfilment
        r.potentials[0].fulfill()
        self.assertEqual(r.fulfilled[0].key, 'a')

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
        a = P('a').reject()
        b = P('b').reject()
        c = P('c').fulfill()

        with self.subTest(part='impossible'):
            with self.assertRaises(RequirementNotMet):
                R(a, b, c, need=5).validate()

        with self.subTest(part='still not enough'):
            with self.assertRaises(RequirementNotMet):
                R(a, b, c, need=2).validate()

        with self.subTest(part='sufficient'):
            R(a, b, c, need=1).validate()

        with self.subTest(part='zero'):
            R(a, b, c, need=0).validate()

    def test_requirement_prioritisation(self):
        r = R('a', 'b', 'c', 'd')
        prioritised = [p.key for p in r.prioritised_potentials(['c', 'b'])]

        self.assertIn('a', prioritised[0:2])
        self.assertIn('d', prioritised[0:2])
        self.assertListEqual(prioritised[2:], ['b', 'c'])

    def test_req_iter(self):
        ids = ['a', 'b', 'c']
        r = R(*ids)
        with self.subTest(part='fulfilled potentials fully listed'):
            self.assertListEqual(r.fulfilled, [])
            [p.fulfill() for p in r.potentials]
            self.assertListEqual([p.item for p in r.fulfilled], ids)

        with self.subTest(part='R object is iterable'):
            self.assertListEqual(list(r), ids)

        with self.subTest(part='R object is indexable'):
            self.assertEqual(r[1], 'b')
