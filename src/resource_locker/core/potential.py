class Potential:
    def __init__(self, item, key_gen=None, **params):
        self._key = item if key_gen is None else key_gen(item)
        self.item = item
        self._is_fulfilled = False
        self._is_rejected = False

    @property
    def key(self):
        return self._key

    @property
    def is_fulfilled(self):
        return self._is_fulfilled

    @property
    def is_rejected(self):
        return self._is_rejected

    def fulfill(self):
        self._is_fulfilled = True
        return self

    def reject(self):
        self._is_rejected = True
        return self

    def reset(self):
        self._is_fulfilled = False
        self._is_rejected = False
        return self
