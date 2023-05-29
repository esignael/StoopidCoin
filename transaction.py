import dilithium.dilithium as dl
import falcon.falcon as fl
import ast
from enum import Enum
from dataclasses import dataclass


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
        schemes = {'D2': dl.Dilithium2,
                   'D3': dl.Dilithium3,
                   'D5': dl.Dilithium5,
                   'F2': fl.Falcon2,
                   'F4': fl.Falcon4,
                   'F8': fl.Falcon8,
                   'F16': fl.Falcon16,
                   'F32': fl.Falcon32,
                   'F64': fl.Falcon64,
                   'F128': fl.Falcon128,
                   'F256': fl.Falcon256,
                   'F512': fl.Falcon512,
                   'F1024': fl.Falcon1024
                   }
        return schemes[self.scheme]

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
