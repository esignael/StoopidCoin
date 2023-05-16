from __future__ import annotations 
import multiprocessing as mp
import secrets as st
import threading as tr
import time
import hashlib as hl
from dataclasses import dataclass


class MetaChain (type):
    def __new__ (cls, name, props, kwargs):
        cls = super().__new__(cls, name, props, kwargs)
        cls._chain_lock = tr.Semaphore()
        cls._chain = []
        return cls

    def __getitem__ (cls, index):
        cls._chain_lock.acquire()
        try:
            return cls._chain[index]
        finally:
            cls._chain_lock.release()

    def __setitem__ (cls, index, value):
        cls._chain_lock.acquire()
        try:
            cls._chain[index] = value
        finally:
            cls._chain_lock.release()

    def __len__ (cls):
        cls._chain_lock.acquire()
        try:
            return len(cls._chain)
        finally:
            cls._chain_lock.release()


@dataclass
class Header ():
    index: int
    challenge: int = 3
    nonce: int = 0
    prev_block: int = 0
    merkle_root: int = 0
    timestamp: float = None

    def __post_init__ (self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def __str__ (self):
        return str(vars(self))

    def __hash__ (self):
        value = hl.sha512(str(self).encode()).digest()
        return int.from_bytes(value, 'big')

    def digest (self):
        return hl.sha512(str(self).encode()).digest()

    def intdigest (self):
        return int.from_bytes(self.digest(), 'big')

    def __mine__ (self):
        while self.intdigest() >> (512 - self.challenge):
            self.nonce = st.randbelow(1 << 512)
        return

    def is_proven (self):
        return self.intdigest() >> (512 - self.challenge)



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


class Block ():
    def __init__ (self, index, merkle, **kwargs):
        self.data = merkle
        self.head = Header(index, merkle_root=merkle.intdigest(), **kwargs)


class BlockChain (metaclass=MetaChain):
    _data_lock = mp.Lock()
    reset_lock = tr.Semaphore()
    _reset = tr.Event()
    ledgers = []
    ledger = MerkleTree()

    def __new_ledger__ (self):
        self._data_lock.acquire()
        try:
            old_ledger = self.ledger
            self.ledger = MerkleTree()
            return old_ledger
        finally:
            self._data_lock.release()

    def __reset_check__ (self):
        with self.reset_lock:
            return self._reset

    def __block_proof__ (self):
        old_ledger = self.__new_ledger__()
        pass

    @classmethod
    def consider (cls, headers):
        if len(headers) <= len(cls):
            return False
        h = set(headers)
        header = cls[::-1]
        for header in cls[::-1]:
            if header in h:
                break
        header.index

        for header in headers[::-1]:
            continue
        #TODO put new header into the chain
        return True

    @classmethod
    def run (cls):
        while 0:
            pass

    @classmethod
    def is_fresh (cls):
        return not cls._reset.is_set()

    @classmethod
    def increment (cls):
        old_ledger = cls.__new_ledger__()
        header = Header()
        while not header.is_proven():
            if cls.is_fresh():
                header.nonce = st.randbelow(1 << 512)
                continue

        pass

    def add_transaction (self, transaction):
        self._data_lock.acquire()
        try:
            self.ledger.append(transaction)
        finally:
            self._data_lock.release()


