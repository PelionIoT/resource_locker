from tests.reporter.base import BaseCase

from resource_locker.reporter import Query, Timer
from resource_locker.reporter import RedisReporter
from resource_locker.reporter import Aspects
from resource_locker.reporter import safe


class Test(BaseCase):
    def setUp(self):
        RedisReporter()._clear_all()

    def test_methods(self):
        tags = dict(
            make='nxp',
            model='k64f'
        )
        r = RedisReporter(**tags)
        r.lock_requested()
        r.lock_success(wait=10.5)
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
            'lock_acquire_wait': 10.5,
            'lock_acquire_fail_count': 1,
            'lock_release_count': 2,
            'lock_release_wait': 50,
            'lock_request_count': 1
        }, q.all_aspects('model', 'k64f'))
        self.assertEqual(50, q.aspect('model', 'k64f', Aspects.lock_release_wait))

    def test_timer_useage(self):
        t = Timer().start()
        r = RedisReporter(x='y')
        r.lock_requested()
        r.lock_success(t.stop())
        q = Query()
        self.assertGreater(q.aspect('x', 'y', Aspects.lock_acquire_wait), 0)

    def test_aspect_valid(self):
        with self.assertRaises(ValueError):
            Aspects.validate('wrong')

    def test_report_failure_expected(self):
        r = RedisReporter(bombproof=False)
        with self.assertRaises(TypeError):
            r.report(tags=1, aspects=None)

    def test_report_failure_muted(self):
        r = RedisReporter(bombproof=True)
        r.report(tags=1, aspects=None)

    def test_safe(self):
        bad_string = 'some.daft-string__match'
        self.assertEqual('some-daft-string--match', safe(bad_string))

    def test_various_tags(self):
        bad_string = 'some.daft-string__match'
        r1 = RedisReporter(a=1, b=2)
        r2 = RedisReporter(a=99, b=2, c=bad_string)

        for i in range(5):
            for r in (r1, r2):
                r.lock_requested(key='lock key')

        q = Query()
        self.assertEqual(10, q.aspect('b', '2', Aspects.lock_request_count))
        self.assertEqual([safe(bad_string)], q.all_values('c'))
        self.assertEqual(sorted(['99', '1']), q.all_values('a'))
