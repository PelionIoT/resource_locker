import logging

import redis_lock
from redis import StrictRedis

from .meta import LockFactoryMeta


class RedisLockFactory(LockFactoryMeta):
    def __init__(self, client=None):
        self.client = client or StrictRedis()
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
