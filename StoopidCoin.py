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
    challange: int = 3
    nonce: int = 0
    prev_block: int = 0
    merkle_root: int = 0

    def __post_init__ (self):
        timestamp = time.time()

    def __str__ (self):
        return str(vars(self))


@dataclass 
class MerkleTree ():
    parent: MerkleTree = None
    left: MerkleTree = None
    right: MerkleTree = None
    value: str = None
    depth: int = 1

    def __post_init__ (self):
        pass

    def __copy__ (self):
        return MerkleTree(**vars(self))

    def __expand__ (self):
        if self.is_leaf():
            return False
        new_arm = MerkleTree(parent=self, depth=self.depth - 1)
        if self.left is None:
            self.left = new_arm
            return True
        if self.right is None:
            self.right = new_arm
            return True
        return False

    def __getitem__ (self, index):
        node_value = pow(2, self.depth-1)
        if index >= (2 * node_value):
            raise IndexError('out of bounds')
        if self.is_leaf():
            return self.value
        if index < node_value:
            if self.left is None:
                raise IndexError('no index left')
            return self.left[index]
        if self.right is None:
            raise IndexError('no index right')
        return self.right[index % node_value]

    def append (self, value):
        if self.is_leaf():
            if self.value is None:
                self.value = value
                return True
            return False
        self.__expand__()
        if not self.is_root():
            return self.left.append(value) or self.right.append(value)
        if self.left.append(value) or self.right.append(value):
            return
        self.left = self.__copy__()
        self.left.parent = self
        self.right = None
        self.left.__finalize__()
        self.depth += 1
        self.append(value)

    @staticmethod
    def int_ (value):
        return int.from_bytes(value, 'big')

    @staticmethod
    def bytes_ (value):
        return value.to_bytes(32, 'big')

    def __hash__ (self):
        sha = hl.sha512()
        if self.is_leaf():
            sha.update(str(self.value).encode())
            return self.int_(sha.digest())
        if self.value is not None:
            return self.value
        sha.update(self.bytes_(hash(self.left)))
        if self.right is not None:
            sha.update(self.bytes_(hash(self.right)))
            return self.int_(sha.digest())
        sha.update(self.bytes_(hash(self.left)))
        return self.int_(sha.digest())

    def __finalize__ (self):
        if self.value is not None:
            return True
        self.left.__finalize__() and self.right.__finalize__()
        self.value = hash(self)
        return True

    def is_leaf (self):
        return self.depth <= 0 
    
    def is_root (self):
        return self.parent is None 

