import socket
import time

from redis import StrictRedis
import redis_lock

from threading import Lock

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


class RequirementNotMet(Exception):
    pass


class Lock:
    lock_of_locks_key = 'lock_of_locks'

    def new_lock(self, key):
        return redis_lock.Lock(StrictRedis(), key)

    def __init__(self, *requirements, expires=120, **params):
        self.options = dict(expires=expires)
        self.options.update(params)

        self.lol = self.new_lock(self.lock_of_locks_key)
        self.attempted = []
        self.requirements = [req if isinstance(req, Requirement) else Requirement(req) for req in requirements]

    def aquire_all(self):
        for requirement in self.requirements:
            for potential in requirement.get_potentials():
                lock = self.new_lock(potential.key)
                self.attempted.append(lock)
                lock.aquire()

    def release_all(self):
        for partial in self.attempted:
            try:
                partial.release()
            except Exception:
                # TODO: logging
                pass

    def aquire(self):
        with self.lol:
            try:
                self.aquire_all()
            finally:
                self.release_all()

    def release(self):
        self.release_all()

    def __enter__(self):
        self.aquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class Requirement:
    def __init__(self, potentials, need=1, **params):
        self.options = dict(need=need)
        self.options.update(params)

        self.need = need
        self.potentials = potentials
        self.lock = Lock()

    def get_potentials(self):
        return self.potentials

    def count(self):
        fulfilled = 0
        rejected = 0
        with self.lock:
            for potential in self.potentials:
                if potential.fulfilled:
                    fulfilled += 1
                if potential.rejected:
                    rejected += 1

    def reject(self, potential):
        with self.lock:
            self.potentials.remove(potential)
            have = len(self.potentials)
            if have < self.need:
                raise RequirementNotMet(f'{have} < {self.need}')


def R(*potentials, **kwargs):
    req = Requirement(potentials, **kwargs)
    for potential in potentials:
        potential.R = req
    return potentials
