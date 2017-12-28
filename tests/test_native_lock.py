from tests.test_redis_lock import Test as RedisTests
from tests.test_redis_contention import Test as RedisContention
from resource_locker import NativeLockFactory


class TestCommon(RedisTests):
    factory_class = NativeLockFactory


class TestContention(RedisContention):
    factory_class = NativeLockFactory
    concurrency = 10
    available = 7
    need = 2
    concurrency_delay = 0.001


# lets not run things twice
del RedisTests
del RedisContention
