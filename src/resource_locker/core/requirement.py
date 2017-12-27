from .exceptions import RequirementNotMet
from .potential import Potential


class Requirement:
    def __init__(self, *potentials, need=None, **params):
        self.options = dict(need=need or 1)
        self.options.update(params)

        self.need = self.options['need']
        self._potentials = []
        self._is_fulfilled = False
        self._is_rejected = False

        for p in potentials:
            self.add_potential(p)

    def __getitem__(self, item):
        return self.fulfilled[item].item

    def __len__(self):
        return len(self.fulfilled)

    def __iter__(self):
        return (item.item for item in self.fulfilled)

    def add_potential(self, p):
        if not isinstance(p, Potential):
            p = Potential(p, **self.options)
        self._potentials.append(p)
        return self

    @property
    def is_fulfilled(self):
        self.validate()
        return self._is_fulfilled

    @property
    def is_rejected(self):
        return self._is_rejected

    @property
    def potentials(self):
        return self._potentials

    @property
    def fulfilled(self):
        return [p for p in self._potentials if p.is_fulfilled]

    def count(self):
        fulfilled = 0
        rejected = 0
        for potential in self._potentials:
            if potential.is_fulfilled:
                fulfilled += 1
            if potential.is_rejected:
                rejected += 1
        return fulfilled, rejected

    def validate(self):
        fulfilled, rejected = self.count()
        if fulfilled >= self.need:
            self._is_fulfilled = True
        else:
            remaining = len(self._potentials) - rejected
            if remaining < self.need:
                self._is_rejected = True
                # right now, requirements are 'AND' (mandatory ... clue is in the name)
                raise RequirementNotMet(f'{remaining} potentials, (need {self.need})')
        return self

    def reset(self):
        self._is_fulfilled = False
        self._is_rejected = False
        for p in self.potentials:
            p.reset()
        return self
