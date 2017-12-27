# Resource Locker
Share your toys, kids

_Resource Locker_ assumes arbitrary resources, each with their own deterministic, unique identifier.
The usage state is retained in a lock server (e.g. a single redis instance, redlock cluster, or similar).
Resources are assumed to be discoverable and filterable by the clients that intend to use them.
This reduces the need to categorise and filter resources on the client's behalf, in comparison to
a resource allocation system with a database of all resources (in which typically only the resource
server is performing discovery).

A comparison of approaches:

| feature | locks only | resource allocator |
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

## Task list
- [x] TODO: reduce fulfilled/rejected to a single tristate rather than two booleans
- [ ] TODO: tagging of keys
- [ ] TODO: logging of lock timings
- [ ] TODO: a better approach to lock acquisition (rather than just marching)
- [ ] TODO: a test to validate high contention behaviour

## Related reading
[mbed Resource Pool?](https://github.com/ARMmbed/resource-pool)
| [DLM](https://en.wikipedia.org/wiki/Distributed_lock_manager)
| [Pareto](https://en.wikipedia.org/wiki/Pareto_efficiency)
| [Ordered locking](http://www.informit.com/articles/article.aspx?p=30188&seqNum=7)
| [Simultaneous locking](http://www.informit.com/articles/article.aspx?p=30188&seqNum=6)