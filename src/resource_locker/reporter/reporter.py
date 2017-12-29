from redis import StrictRedis

"""The reporter will track and record the amount of time
spent waiting for or using locks.

It must record enough information for another system to optimise
the number of resources over time.

A potential approach:
ontological tags have values i.e. k-v pairs
additionally, the 'key' tag for each lock
- store each unique k encountered
  - store the timing info against this key
- store each unique k-v encountered
  - store the timing info against this key
where timing info is acquire time, release time, duration, count

in reality, for redis, this means t-k-v triples
we can only use counters on top level keys
so what would make sense is a hash for every tag
this hash would store keys of 
"""

tags_collection = '_TAGS'
key_template = '_TAG_{key}'
key_value_template = '{key}__{value}'


class Aspects:
    lock_request_count = 'lock_request_count'
    lock_acquire_count = 'lock_acquire_count'
    lock_release_count = 'lock_release_count'
    lock_release_wait = 'lock_release_wait'
    lock_acquire_wait = 'lock_acquire_wait'
    lock_acquire_fail_count = 'lock_acquire_fail_count'

    @staticmethod
    def validate(*aspects):
        for aspect in aspects:
            if not hasattr(Aspects, aspect):
                raise ValueError(f'aspect {repr(aspect)} not supported')


def safe(thing):
    return str(thing).strip().lower().replace('.', '-').replace(':', '-').replace('_', '-')


class Query:
    def __init__(self):
        self.client = StrictRedis(db=1)

    def all_tags(self):
        return sorted([s.decode() for s in self.client.smembers(tags_collection)])

    def all_values(self, tag):
        return sorted([s.decode() for s in self.client.smembers(key_template.format(key=safe(tag)))])

    def all_aspects(self, tag, value):
        return {
            k.decode(): int(v) for k, v in
            self.client.hgetall(key_value_template.format(key=safe(tag), value=safe(value))).items()
        }

    def aspect(self, tag, value, aspect):
        Aspects.validate(aspect)
        return int(self.client.hget(key_value_template.format(key=safe(tag), value=safe(value)), aspect))


class Reporter:
    def __init__(self, client=None, **tags):
        self.client = client or StrictRedis(db=1)
        self.tags = tags

    def _clear_all(self):
        self.client.flushdb()

    def _increment_all(self, tags, aspects):
        Aspects.validate(*list(aspects))
        self.client.sadd(tags_collection, *list(tags.keys()))
        for key, value in tags.items():
            value = safe(value)
            key = safe(key)
            lookup_key = key_template.format(key=key)
            self.client.sadd(lookup_key, value)
            store_key = key_value_template.format(key=key, value=value)
            for aspect, incr in aspects.items():
                self.client.hincrby(store_key, aspect, incr)
        return len(tags) * len(aspects)

    def _report(self, tags, aspects):
        request = {}
        request.update(self.tags)
        request.update(tags)
        return self._increment_all(request, aspects)

    def lock_requested(self, **tags):
        self._report(tags, {Aspects.lock_request_count: 1})

    def lock_success(self, wait: int, **tags):
        self._report(tags, {Aspects.lock_acquire_count: 1, Aspects.lock_acquire_wait: wait})

    def lock_failed(self, **tags):
        self._report(tags, {Aspects.lock_acquire_fail_count: 1})

    def lock_released(self, wait: int, **tags):
        self._report(tags, {Aspects.lock_release_count: 1, Aspects.lock_release_wait: wait})
