import redis_lock
from redis import StrictRedis
from abc import ABC
from abc import abstractmethod

from threading import Lock
import logging


class LockFactoryMeta(ABC):
    @abstractmethod
    def new_lock(self, key, **params):
        """Must return an object with a Lock-like interface"""
        pass

    @abstractmethod
    def get_lock_list(self):
        """Must return a list of string keys of existing locks"""
        pass

    @abstractmethod
    def clear_all(self):
        """Must clear all locks from the system (primarily for testing)"""
        pass


class NativeLockFactory(LockFactoryMeta):
    """Demonstrates use of alternative lock implementations"""
    def __init__(self, *args, **kwargs):
        self.all_locks = {}

    def new_lock(self, key, **params):
        # override the lock factory to use local locks instead! faster! wooooo!
        # also somewhat validates backend-agnostic approach
        return self.all_locks.setdefault(key, Lock())

    def get_lock_list(self):
        return list(self.all_locks.keys())

    def clear_all(self):
        self.all_locks.clear()


class RedisLockFactory(LockFactoryMeta):
    def __init__(self, *args, **kwargs):
        self.client = StrictRedis(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def new_lock(self, key, **params):
        """Creates a new lock with a lock manager"""
        opts = {k: v for k, v in params.items() if k in {'expire', 'auto_renewal'}}
        return redis_lock.Lock(self.client, name=key, **opts)

    def get_lock_list(self):
        """Gets a list of live locks to optimise acquisition attempts"""
        prefix = 'lock:'
        return [k.decode('utf8').split(':', 1)[1] for k in self.client.keys(f'{prefix}*')]

    def clear_all(self):
        """Clears all locks"""
        self.logger.critical('caution: clearing all locks; collision safety is voided')
        redis_lock.reset_all(self.client)


default_lock_factory = RedisLockFactory()
