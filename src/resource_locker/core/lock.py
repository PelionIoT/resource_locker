from redis import StrictRedis
import redis_lock

import logging

import retrying

from .exceptions import RequirementNotMet
from .requirement import Requirement


class Lock:
    lock_of_locks_key = 'lock_of_locks'

    def new_lock(self, key, **params):
        """Creates a new lock with a lock manager"""
        self.lock_instance = StrictRedis()
        opts = {k: v for k, v in params.items() if k in {'expire', 'auto_renewal'}}
        return redis_lock.Lock(self.lock_instance, name=key, **opts)

    def get_lock_list(self):
        """Gets a list of live locks to optimise acquisition attempts"""
        prefix = 'lock:'
        return [k.decode('utf8').split(':', 1)[1] for k in self.lock_instance.keys(f'{prefix}*')]

    def clear_all(self):
        """Clears all locks"""
        self.logger.critical('caution: clearing all locks; collision safety is voided')
        redis_lock.reset_all(StrictRedis())

    def __init__(self, *requirements, **params):
        self.options = dict(
            logger=logging.getLogger(__name__),
            # lock configuration (see https://pypi.python.org/pypi/python-redis-lock)
            auto_renewal=True,
            expire=120,
            timeout=None,
            # retry configuration (see https://pypi.python.org/pypi/retrying)
            stop_max_delay=30000,
            wait_exponential_max=10000,
            wait_exponential_multiplier=1500,
        )
        self.options.update(params)

        self.timeout = self.options['timeout']
        self.logger = self.options['logger']

        self.lol = self.new_lock(self.lock_of_locks_key, expire=60, auto_renewal=bool(self.timeout))
        self.obtained = []
        self.requirements = []
        self.unique_keys = set()

        # list of all keys that are locked. we should ask the lockserver for this at the start.
        self.known_locked_keys = []

        # reserved for implementation of different Lock backends
        self.lock_instance = None

        for req in requirements:
            self.add_requirement(req)

    def add_requirement(self, req):
        if not isinstance(req, Requirement):
            req = Requirement(req, need=self.options.get('need'))
        req.validate()
        for p in req.potentials:
            if p.key in self.unique_keys:
                raise ValueError(f'Must have unique keys, got two {repr(p.key)}')
            self.unique_keys.add(p.key)
        self.requirements.append(req)

    def _acquire_one(self, potential):
        if potential.is_fulfilled or potential.is_rejected:
            self.logger.info(
                'potential %s is already %s',
                potential,
                'fulfilled' if potential.is_fulfilled else 'rejected'
            )
            return
        lock = self.new_lock(potential.key, **self.options)
        acq_kwargs = dict(blocking=bool(self.timeout))
        if self.timeout:
            acq_kwargs.update(dict(timeout=self.timeout))
        self.logger.info('getting %s, timeout %s', potential.key, self.timeout)
        acquired = lock.acquire(**acq_kwargs)
        if acquired:
            potential.fulfill()
            self.obtained.append(lock)
        else:
            potential.reject()
            self.logger.warning('didnt get lock %s', potential.key)

    def _acquire_all(self):
        for requirement in self.requirements:
            for potential in requirement.potentials:
                if requirement.is_fulfilled or requirement.is_rejected:
                    break
                self._acquire_one(potential=potential)
            if not requirement.is_fulfilled:
                raise RequirementNotMet('cannot meet all requirements')
        return self.requirements

    def _release_all(self):
        for partial in self.obtained:
            try:
                partial.release()
            except Exception:
                self.logger.exception('partial lock release failed')
        self.obtained.clear()
        for r in self.requirements:
            r.reset()

    def acquire(self):
        # simultaneous locking
        # alternatively, try ordered locking
        with self.lol:
            try:
                return self._acquire_all()
            except Exception:
                self.logger.warning('lock acquisition failed, releasing all partial locks')
                self._release_all()
                raise

    def release(self):
        self._release_all()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
