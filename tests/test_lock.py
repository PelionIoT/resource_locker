from tests.test_redis_lock import Test as RedisTestCase

from resource_locker import Lock

from threading import Lock as tLock
all_locks = {}


class LocalDLock(Lock):
    def new_lock(self, key, **params):
        # override the lock factory to use local locks instead! faster! wooooo!
        # also somewhat validates backend-agnostic approach
        return all_locks.setdefault(key, tLock())

    def get_lock_list(self):
        return list(all_locks.keys())

    def clear_all(self):
        all_locks.clear()


class Test(RedisTestCase):
    lock_class = LocalDLock


# lets not run things twice
del RedisTestCase
