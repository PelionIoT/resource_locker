import socket
import time

from redis import StrictRedis
import redis_lock

from threading import Lock

"""

host_id = "owned-by-%s" % socket.gethostname()

print('owner', host_id)
conn = StrictRedis()
with redis_lock.Lock(conn, "name-of-the-lock", id=host_id):
    print("Got the lock. Doing some work ...")
    time.sleep(5)


# from redlock import RedLockFactory
# factory = RedLockFactory(
#     connection_details=[
#         {'host': 'xxx.xxx.xxx.xxx'},
#         {'host': 'xxx.xxx.xxx.xxx'},
#         {'host': 'xxx.xxx.xxx.xxx'},
#         {'host': 'xxx.xxx.xxx.xxx'},
#     ])

# example usage
Lock = LockFactory([conn], default_args_such_as, autorenew=True, expires=120)
devices = R(D1, D2, D3, need=2)  # ORs devices
org = R(O1, O2, need=1)  # (1 default)

# future: combine ORs and ANDs, and other combinatorics

with Lock(devices, org, expires=600) as obtained:  # ANDs R objects
    # doing a test using a specific device and organisation
    # on success or failure, lock is released
    # on crash, lock will eventually timeout

    obtained[0] == devices
    obtained[1] == org

    org['id']  # just works - org was not a list
    for device in devices:
        device['id']  # devices was a list, because n > 1
"""


class RequirementNotMet(Exception):
    pass


class Lock:
    lock_of_locks_key = 'lock_of_locks'

    def new_lock(self, key, **params):
        opts = {k:v for k, v in params.items() if k in {'expire', 'auto_renewal'}}
        return redis_lock.Lock(StrictRedis(), name=key, **opts)

    def __init__(self, *requirements, **params):
        self.options = dict(expire=120, auto_renewal=True, timeout=None)
        self.options.update(params)

        self.timeout = self.options.get('timeout')

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
                print('getting', potential.key, self.timeout)
                acquired = lock.acquire(**acq_kwargs)
                if acquired:
                    potential.fulfill()
                    self.obtained.append(lock)
                else:
                    potential.reject()
                    print('didnt get lock', potential.key)
                requirement.validate()
            if not requirement.is_fulfilled:
                raise RequirementNotMet('cannot meet all requirements')
        return self.requirements

    def _release_all(self):
        for partial in self.obtained:
            try:
                partial.release()
            except Exception as e:
                # TODO: logging
                print('release failed', e)
                pass
        self.obtained.clear()
        for r in self.requirements:
            r.reset()

    def acquire(self):
        # simultaneous locking
        # alternatively, try ordered locking
        with self.lol:
            try:
                return self._acquire_all()
            except Exception as e:
                # TODO: logging
                print('release all', e)
                self._release_all()
                raise

    def release(self):
        self._release_all()

    @staticmethod
    def clear_all():
        print('warning: clearing all locks')
        redis_lock.reset_all(StrictRedis())

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class Requirement:
    def __init__(self, *potentials, need=None, **params):
        self.options = dict(need=need or 1)
        self.options.update(params)

        self.need = self.options['need']
        self.potentials = []
        self._fulfilled = False
        self._rejected = False

        for p in potentials:
            self.add_potential(p)

    def __getitem__(self, item):
        return self.items[item].item

    def add_potential(self, p):
        if not isinstance(p, Potential):
            p = Potential(p, **self.options)
        self.potentials.append(p)

    @property
    def is_fulfilled(self):
        return self._fulfilled

    @property
    def is_rejected(self):
        return self._rejected

    def get_potentials(self):
        return self.potentials

    @property
    def items(self):
        return [p for p in self.potentials if p.is_fulfilled]

    def count(self):
        fulfilled = 0
        rejected = 0
        for potential in self.potentials:
            if potential.is_fulfilled:
                fulfilled += 1
            if potential.is_rejected:
                rejected += 1
        return fulfilled, rejected

    def validate(self):
        fulfilled, rejected = self.count()
        if fulfilled >= self.need:
            self._fulfilled = True
        else:
            remaining = len(self.potentials) - rejected
            if remaining < self.need:
                self._rejected = True
                # right now, requirements are 'AND' (mandatory ... clue is in the name)
                raise RequirementNotMet(f'{remaining} potentials, (need {self.need})')

    def reset(self):
        self._fulfilled = False
        self._rejected = False
        for p in self.get_potentials():
            p.reset()


class Potential:
    def __init__(self, item, key_gen=None, **params):
        self._key = item if key_gen is None else key_gen(item)
        self.item = item
        self.is_fulfilled = False
        self.is_rejected = False

    @property
    def key(self):
        return self._key

    def fulfill(self):
        self.is_fulfilled = True

    def reject(self):
        self.is_rejected = True

    def reset(self):
        self.is_fulfilled = False
        self.is_rejected = False
