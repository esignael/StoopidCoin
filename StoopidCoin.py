from __future__ import annotations 
import multiprocessing as mp
import secrets as st
import queue as qu
import threading as tr
import time
import hashlib as hl
from dataclasses import dataclass
from constants import *


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

class LockableList ():
    def __init__ (self, *args, **kwargs):
        self.__list__ = list(*args, **kwargs)
        self.__lock__ = tr.Semaphore()

        @property
        def lock (self):
            return self.__lock__


@dataclass
class Header ():
    index: int = 0
    challenge: int = INIT_CHALLENGE
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

    def mine (self):
        self.__mine__()
        return self.nonce

    def __mine__ (self):
        while self.intdigest() >> (512 - self.challenge):
            self.nonce = st.randbelow(1 << 512)
        return

    def is_proven (self):
        return not (self.intdigest() >> (512 - self.challenge))


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


class BlockChain ():
    def __init__ (self, headers=None, ledgers=None):
        self.__ledger_lock__ = tr.Lock()
        self.__header_lock__ = tr.Lock()
        self.step = tr.Event()
        self.queue = qu.Queue()
        self.queue.put(MerkleTree())
        if ledgers is None:
            ledgers = [None]
        if headers is None:
            headers = [Header(timestamp=0, nonce=INIT_NONCE)]
        self.headers = headers
        self.ledgers = ledgers

    def consensus (self, new_chain):
        self.__header_lock__.acquire()
        self.__ledger_lock__.acquire()
        try: 
            if len(new_chain) <= len(self.header):
                return False
            self.__update_chain__(new_block)
            return True
        finally:
            self.__ledger_lock__.release()
            self.__header_lock__.release()

    def __update_chain__ (self, new_chain):
        for header in self.headers[::-1]:
            if header in new_chain:
                break
        index = header.index
        self.headers[index:] = new_chain[index:]
        self.ledgers[index:] = [None] * len(header_list[index:])

    def add_transaction (self, transaction):
        self.step.clear()
        if not transaction.verify():
            return False
        current_ledger = self.queue.get()
        current_ledger.append(transaction)
        self.queue.put(current_ledger)
        self.queue.task_done()
        self.step.set()
        return True

    def queue_nowait (self, ledger):
        try:
            self.queue.put_nowait(ledger)
        except qu.Full:
            return 

    def main (self, callback):
        thread = tr.Thread(target=self.mine, args=(callback,))
        thread.start()

    def mine (self, callback):
        while True:
            self.__header_lock__.acquire()
            try:
                self.step.wait()
                current_ledger = self.queue.get()
                header = self._create_header_(current_ledger)
                self.queue.task_done()
                if not header.is_proven():
                    self.queue_nowait(current_ledger)
                    continue
                self.headers.append(header)
                self.ledgers.append(current_ledger)
                self.queue.put(MerkleTree())
                if callback is not None:
                    callback()
            finally:
                self.__header_lock__.release()

    def _create_header_ (self, merkle):
        prev = self.headers[-1].digest()
        nonce = st.randbelow(1 << 512)
        return Header(prev_block=prev, nonce=nonce, merkle_root=merkle)

