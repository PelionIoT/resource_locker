from tests.test_redis_lock import Test as CommonTest  # noqa
from tests.test_contention import Test as RedisContention
from resource_locker.core.factory import NativeLockFactory
import resource_locker

previously = None


def setUpModule():
    global previously
    previously = resource_locker.core.factory.default_lock_factory
    resource_locker.core.factory.default_lock_factory = NativeLockFactory()


def tearDownModule():
    resource_locker.core.factory.default_lock_factory = previously


class TestContention(RedisContention):
    concurrency = 10
    available = 7
    need = 2
    concurrency_delay = 0.001


# lets not run things twice
del RedisContention
