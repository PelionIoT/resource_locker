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
