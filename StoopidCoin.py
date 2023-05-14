from __future__ import annotations 
import time
import hashlib as hl
from dataclasses import dataclass


class MetaList (type):
    def __new__ (cls, name, props, kwargs):
        cls = super().__new__(cls, name, props, kwargs)
        cls.instances = []
        return cls

    def __getitem__ (cls, index):
        return cls.instances[index]


class Listed (metaclass=MetaList):
    pass 


@dataclass
class Header ():
    index: int
    challange: int
    nonce: int
    prev_block: int
    merkle_root: hash

    def __post_init__ (self):
        timestamp = time.time()

    def __str__ (self):
        return str(vars(self))


@dataclass
class Body ():
    transactions: list


@dataclass 
class MerkleTree ():
    parent: MerkleTree = None
    left: MerkleTree = None
    right: MerkleTree = None
    value: str = None

    def add (self, leaf):
        new = MerkleTree()
        new.left = self
        self.parent = new
        self.value = leaf
        self = new
        return self, new

    def is_leaf (self):
        return not isinstance(self.left, MerkleTree)
