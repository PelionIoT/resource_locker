from threading import Lock

from .meta import LockFactoryMeta


class NativeLockFactory(LockFactoryMeta):
    """Demonstrates use of alternative lock implementations"""
    def __init__(self):
        self.all_locks = {}

    def new_lock(self, key, **params):
        # override the lock factory to use local locks instead! faster! wooooo!
        # also somewhat validates backend-agnostic approach
        return self.all_locks.setdefault(key, Lock())

    def get_lock_list(self):
        return list(self.all_locks.keys())

    def clear_all(self):
        self.all_locks.clear()
