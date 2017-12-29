from tests.reporter.base import BaseCase

from resource_locker.reporter.reporter import Query
from resource_locker.reporter.reporter import Reporter
from resource_locker.reporter.reporter import Aspects
from resource_locker.reporter.reporter import safe


class Test(BaseCase):
    def setUp(self):
        Reporter()._clear_all()

    def test(self):
        tags = dict(
            make='nxp',
            model='k64f'
        )
        r = Reporter(**tags)
        r.lock_requested()
        r.lock_success(wait=10)
        r.lock_released(wait=25)
        r.lock_released(wait=25)
        r.lock_failed()
        q = Query()
        self.assertEqual(sorted(list(tags.keys())), q.all_tags())
        self.assertEqual(['nxp'], q.all_values('make'))
        self.assertEqual(['k64f'], q.all_values('model'))
        self.assertEqual(['k64f'], q.all_values('model'))
        self.assertEqual({
            'lock_acquire_count': 1,
            'lock_acquire_wait': 10,
            'lock_acquire_fail_count': 1,
            'lock_release_count': 2,
            'lock_release_wait': 50,
            'lock_request_count': 1
        }, q.all_aspects('model', 'k64f'))
        self.assertEqual(50, q.aspect('model', 'k64f', Aspects.lock_release_wait))

    def test_aspect_valid(self):
        with self.assertRaises(ValueError):
            Aspects.validate('wrong')

    def test_safe(self):
        bad_string = 'some.daft-string__match'
        self.assertEqual('some-daft-string--match', safe(bad_string))

    def test_various_tags(self):
        bad_string = 'some.daft-string__match'
        r1 = Reporter(a=1, b=2)
        r2 = Reporter(a=99, b=2, c=bad_string)

        for i in range(5):
            for r in (r1, r2):
                r.lock_requested(key='lock key')

        q = Query()
        self.assertEqual(10, q.aspect('b', '2', Aspects.lock_request_count))
        self.assertEqual([safe(bad_string)], q.all_values('c'))
        self.assertEqual(sorted(['99', '1']), q.all_values('a'))
