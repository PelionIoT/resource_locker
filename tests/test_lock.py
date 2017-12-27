from tests.test_redis_lock import Test as RedisTestCase

from resource_locker import Lock

from threading import Lock as tLock
all_locks = {}


class LocalDLock(Lock):
    def new_lock(self, key, **params):
        # override the lock factory to use local locks instead! faster! wooooo!
        # also somewhat validates backend-agnostic approach
        return all_locks.setdefault(key, tLock())


class Test(RedisTestCase):
    lock_class = LocalDLock


# lets not run things twice
del RedisTestCase
