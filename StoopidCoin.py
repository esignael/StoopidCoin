from __future__ import annotations 
import multiprocessing as mp
import secrets as st
import queue as qu
import threading as tr
import time
import hashlib as hl
from dataclasses import dataclass
from constants import *


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
        self.chain_lock = self.__header_lock__ = tr.Lock()
        self.check = self.step = tr.Event()
        self.ledger = self.queue = qu.Queue()
        self.queue.put(MerkleTree())
        if ledgers is None:
            ledgers = [None]
        if headers is None:
            headers = [Header(timestamp=0, nonce=INIT_NONCE)]
        self.headers = headers
        self.ledgers = ledgers

    def consensus (self, new_chain):
        self.chain_lock.acquire()
        try: 
            return self._update_chain_(new_chain)
        finally:
            self.chain_lock.release()

    def _update_chain_ (self, new_chain):
        if len(new_chain) <= len(self.headers):
            return False
        for header in self.headers[::-1]:
            if header in new_chain:
                break
        index = header.index
        self.headers[index:] = new_chain[index:]
        self.ledgers[index:] = [None] * len(header_list[index:])
        self._clear_ledger_()
        return True

    def _clear_ledger_ (self):
        self.ledger.get()
        self.ledger.put(MerkleTree())

    def add_to_ledger (self, transaction):
        self.check.clear()
        try:
            return self._add_to_ledger_(transaction)
        finally:
            self.check.set()

    def _add_to_ledger_ (self, transaction):
        if not transaction.verify():
            return None
        ledger = self.ledger.get()
        ledger.append(transaction)
        self.ledger.put(ledger)
        return ledger

    def start_mining (self, callback=lambda : None):
        thread = tr.Thread( target=self._loop_, args=(callback,))
        thread.start()

    def _loop_ (self, callback):
        while True:
            self.chain_lock.acquire()
            try:
                self.check.wait()
                self._new_header_(callback)
            finally:
                self.chain_lock.release()

    def _new_header_ (self, callback):
        ledger = self.ledger.get()
        try:
            prev_hash = self.headers[-1].digest()
            nonce = st.randbelow(1 << 512)
            new_header = Header(prev_block=prev_hash, nonce=nonce, merkle_root=hash(ledger))
            if not new_header.is_proven():
                return
            self.headers.append(new_header)
            self.ledgers.append(ledger)
            ledger = MerkleTree()
            callback()
        finally:
            self.ledger.put(ledger)

