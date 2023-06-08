import ast
import hashlib as ha
import constants as ct
import math
import multiprocessing as mp
import secrets as st
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
        return self.intdigest()

    def digest (self):
        return hl.sha512(str(self).encode()).digest()

    def intdigest (self):
        return int.from_bytes(self.digest(), 'big')

    def is_proven (self):
        return not (self.intdigest() >> (512 - self.challenge))


class Merkle ():
    def __init__ (self, digests=None):
        self._digests_ = digests
        self.__update__()

    def __update__ (self):
        self._digest = self._digest_()

    @classmethod
    def from_intdigest (cls, digest_list):
        main = [digest.to_bytes(512//8, 'big') for digest in digest_list]
        return Merkle(main)

    def append (self, item):
        self.digests.append(item)
        self.__update__()

    def _digest_ (self, index=0):
        length = self._length_ = len(self._digests_)
        self._depth_ = math.ceil(math.log(self._length_, 2))
        depth = math.ceil(math.log(length, 2))
        working = [None] * 2 ** depth
        working[:length] = self.digests
        for level in range(depth):
            lhs = working[::2]
            rhs = working[1::2]
            working = [self.concat(lhs[i], rhs[i]) for i in range(len(rhs))]
        return working[0]

    def digest (self):
        return self._digest

    def intdigest (self):
        return int.from_bytes(self.digest(), 'big')

    @property
    def digests (self):
        return self._digests_[:]

    @property
    def intdigests (self):
        return [int.from_bytes(item, 'big') for item in self._digests_]

    def concat (self,lhs, rhs):
        sha = hl.sha512()
        if lhs is None:
            return None
        sha.update(lhs)
        if rhs is None:
            rhs = lhs
        sha.update(rhs)
        return sha.digest()


class BlockChain ():
    def __init__ (self, headers=None, ledgers=None):
        if ledgers is None:
            ledgers = [None]
        if headers is None:
            headers = [Header(timestamp=0, nonce=INIT_NONCE)]
        self.headers = headers
        self.ledgers = ledgers

    def append (self, header, ledger):
        self.headers.append(header)
        self.ledgers.append(ledger)
        pass


@dataclass
class Transaction ():
    sender: bytes
    receiver: bytes
    scheme: str
    amount: float
    signature: bytes = None

    def __str__ (self):
        return str(vars(self))

    @property
    def backend (self):
        return ct.BACKEND[self.scheme]

    def message (self):
        values = vars(self)
        return str({key: values[key] for key in values if key != 'signature'})

    def sign (self, sk):
        self.signature = self.backend.sign(sk, self.message().encode())

    def verify (self):
        return self.backend.verify(self.sender, self.message().encode(), self.signature)

    @classmethod
    def from_rep (cls, rep):
        return cls(**ast.literal_eval(rep))

    def digest (self):
        return ha.sha512(str(self).encode()).digest()

    def intdigest (self):
        return int.from_bytes(self.digest(), 'big')

    def __hash__ (self):
        return self.intdigest()


if __name__ == '__main__':
    pk, sk = dl.Dilithium5.keygen()
    m =b'wow, that really works'
    a = Transaction(pk, pk, 'D5', 10.5)
    #print(a.message())
    pk1, sk1 = fl.Falcon512.keygen()
    r = fl.SecretKey(512)
    sk2 = [r.f,r.g,r.F,r.G]
    print('now')
    b = fl.Falcon512.sign(sk2, m)
    print(b)
    print(r.verify(m, b))
    exit()
    print(pk1)
    print(sk1)
    #print(a.sign(sk))
    #print(a.verify())
