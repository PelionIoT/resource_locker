from redis import StrictRedis
import redis_lock

import logging

from .exceptions import RequirementNotMet
from .requirement import Requirement


class Lock:
    lock_of_locks_key = 'lock_of_locks'

    def new_lock(self, key, **params):
        opts = {k:v for k, v in params.items() if k in {'expire', 'auto_renewal'}}
        return redis_lock.Lock(StrictRedis(), name=key, **opts)

    def __init__(self, *requirements, **params):
        self.options = dict(expire=120, auto_renewal=True, timeout=None, logger=logging.getLogger(__name__))
        self.options.update(params)

        self.timeout = self.options['timeout']
        self.logger = self.options['logger']

        self.lol = self.new_lock(self.lock_of_locks_key, expire=60, auto_renewal=bool(self.timeout))
        self.obtained = []
        self.requirements = []
        self.unique_keys = set()

        # list of all keys that are locked. we should ask the lockserver for this at the start.
        self.known_locked_keys = []

        for req in requirements:
            self.add_requirement(req)

    def add_requirement(self, req):
        if not isinstance(req, Requirement):
            req = Requirement(req, need=self.options.get('need'))
        req.validate()
        for p in req.get_potentials():
            if p.key in self.unique_keys:
                raise ValueError(f'Must have unique keys, got two {repr(p.key)}')
            self.unique_keys.add(p.key)
        self.requirements.append(req)

    def _acquire_all(self):
        for requirement in self.requirements:
            for potential in requirement.get_potentials():
                if requirement.is_fulfilled:
                    break
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
                requirement.validate()
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

    def clear_all(self):
        self.logger.critical('caution: clearing all locks; collision safety is voided')
        redis_lock.reset_all(StrictRedis())

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
