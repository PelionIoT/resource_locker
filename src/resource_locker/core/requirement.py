from .exceptions import RequirementNotMet
from .potential import Potential


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
