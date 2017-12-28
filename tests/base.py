import unittest
import logging

from resource_locker import Lock
from resource_locker import NativeLockFactory

from functools import partial

logging.basicConfig(level=logging.INFO)


class BaseCase(unittest.TestCase):
    lock_class = Lock
    factory_class = NativeLockFactory

    @classmethod
    def setUpClass(cls):
        cls.factory = cls.factory_class()
        cls.lock_class = partial(cls.lock_class, block=False, lock_factory=cls.factory)
