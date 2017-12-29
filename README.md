# Resource Locker
Share your toys, kids

_Resource Locker_ assumes arbitrary resources, each with their own deterministic, unique identifier.
The usage state is retained in a lock server (e.g. a single redis instance, redlock cluster, or similar).
Resources are assumed to be discoverable and filterable by the clients that intend to use them.
This reduces the need to categorise and filter resources on the client's behalf, in comparison to
a resource allocation system with a database of all resources (in which typically only the resource
server is performing discovery).

A comparison of approaches:

| feature | locks only | resource server |
|-|:-|-|
| Collision protection | Y | Y |
| Lease timeout | Y | Y |
| Resource database | N | Y |
| Server-side resource filtering | N | Y |
| Arbitrary resource types | Y | Maybe (depends on db schema) |
| Pool growth/reduction | N (SoC*, other service) | Maybe (ideally SoC, but often mixed in) |
| Discovery queries | O(C**) | O(1) |

(*separation of concerns, **number of clients)

In practise, the intent is for resource sharing between parallel testruns on a constrained resource pool.
A separate service tracks resource presence, so discovery (querying for them) is assumed to be trivial. 

[GitHub repo](https://github.com/ARMmbed/resource_locker)

## Install
This might work?

`pipenv install -e git+https://github.com/ARMmbed/resource_locker.git#egg=resource_locker`

## Usage

### Locking
```python
# some resource thing
devices = list_connected_devices()

from resource_locker import Lock, R, P
from operator import attrgetter
req1 = R(*devices, need=2, key_gen=attrgetter('id'))
req2 = R(P('this one thing'))
with Lock(req1, req2, 'other thing') as obtained:
    print(obtained[0][0]) # first requirement, first device
    print(obtained[0][1]) # first requirement, second device
    print(obtained[2][0]) # `other thing`
    
    # alternatively
    req1[1]  # second device
    req2[0]  # 'this one thing'
```
#### Configuration
Lock backend can be configured as follows:

```python
from redis import StrictRedis
from resource_locker import RedisLockFactory
from resource_locker import Lock
custom = RedisLockFactory(client=StrictRedis(db=7))
Lock('a', lock_factory=custom)
```

### Reporting
The `RedisReporter` class can be used to track lock usage automatically:

```python
import time
from resource_locker import reporter
from resource_locker import Lock
from resource_locker import P
with Lock(P('a', model='T1000'), reporter_class=reporter.RedisReporter):
    time.sleep(1)
reporter.Query().all_tags()  # ['key', 'model']
reporter.Query().all_values('model')  # ['T1000']
reporter.Query().all_aspects('model', 'T1000') # ...

{'lock_acquire_count': 1,
 'lock_acquire_wait': 0.008001565933228,
 'lock_release_count': 1,
 'lock_release_wait': 1.000413179397583,
 'lock_request_count': 1}
```

#### Configuration
Reporter backend can be configured as follows:
```python
from functools import partial
from redis import StrictRedis
from resource_locker import reporter
from resource_locker import Lock
client = StrictRedis(db=9)
custom_reporter = partial(reporter.RedisReporter, client=client)
Lock(reporter_class=custom_reporter)
```

## Task list
- [x] TODO: reduce fulfilled/rejected to a single tristate rather than two booleans
- [x] TODO: a better approach to lock acquisition (rather than just marching)
- [x] TODO: a test to validate high contention behaviour
- [x] TODO: setup.py
- [x] TODO: logging of lock timings
- [x] TODO: tagging of keys
- [ ] TODO: integrate with testrunner
- [ ] TODO: probably fix the weird argument/options stuff?

## Related reading
[mbed Resource Pool?](https://github.com/ARMmbed/resource-pool)
| ["RaaS" client](https://github.com/ARMmbed/raas-pyclient)
| [DLM](https://en.wikipedia.org/wiki/Distributed_lock_manager)
| [Pareto](https://en.wikipedia.org/wiki/Pareto_efficiency)
| [Ordered locking](http://www.informit.com/articles/article.aspx?p=30188&seqNum=7)
| [Simultaneous locking](http://www.informit.com/articles/article.aspx?p=30188&seqNum=6)
