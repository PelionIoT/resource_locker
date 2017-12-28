from abc import ABC, abstractmethod


class LockFactoryMeta(ABC):
    @abstractmethod
    def new_lock(self, key, **params):
        """Must return an object with a Lock-like interface"""

    @abstractmethod
    def get_lock_list(self):
        """Must return a list of string keys of existing locks"""

    @abstractmethod
    def clear_all(self):
        """Must clear all locks from the system (primarily for testing)"""
