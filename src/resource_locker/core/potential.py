class Potential:
    def __init__(self, item, key_gen=None, tag_gen=None, tags=None, **more_tags):
        self.item = item
        self._state = None
        self._key = item if key_gen is None else key_gen(item)

        self._tags = dict(key=self._key)
        if tags:
            self._tags.update(tags)
        self._tags.update(more_tags)
        if tag_gen:
            self._tags.update(tag_gen(item))

    @property
    def key(self):
        return self._key

    @property
    def tags(self):
        return self._tags

    @property
    def is_fulfilled(self):
        return self._state is True

    @property
    def is_rejected(self):
        return self._state is False

    def fulfill(self):
        self._state = True
        return self

    def reject(self):
        self._state = False
        return self

    def reset(self):
        self._state = None
        return self
