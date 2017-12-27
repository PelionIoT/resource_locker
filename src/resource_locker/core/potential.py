class Potential:
    def __init__(self, item, key_gen=None, **params):
        self._key = item if key_gen is None else key_gen(item)
        self.item = item
        self._state = None

    @property
    def key(self):
        return self._key

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
