import time
from constants import *
from dataclasses import dataclass
from transaction import Transaction
import threading as tr
import StoopidCoin as stc
import paho.mqtt.client as mqtt
import ast
import dilithium.dilithium as dl
import json 
import secrets as sc


@dataclass
class Node ():
    scheme: str
    def __post_init__ (self):
        self.public, self.private = BACKEND[self.scheme].keygen()
        self.addresses = []
        self.__init_client__()
        self.client.subscribe(DISTRIBUTION_TOPIC)
        self.client.publish(DISTRIBUTION_TOPIC, str(self.public))
        self.blockchain = stc.BlockChain()
        self.name = f'[Node {str(hash(self.public))[:4]}]'

    def __init_client__ (self):
        self.client = mqtt.Client()
        self.client.on_message = self.__on_message__
        self.client.connect(BROKER, PORT)
        self.client.loop_start()

    def __on_message__ (self, client, userdata, package):
        message = package.payload.decode()

        if package.topic == DISTRIBUTION_TOPIC:
            self.__distribution_callback__(message)

        elif package.topic == TRANSACTION_TOPIC:
            self._transaction_callback_(message)

        elif package.topic == BLOCKCHAIN_TOPIC:
            self._block_callback_(message)
        else:
            # UNKNOWN TOPIC AT THIS POINT
            assert False

    def __distribution_callback__ (self, message):
        public_key = ast.literal_eval(message)
        if public_key in self.addresses:
            return
        if public_key == self.public:
            return
        self.addresses.append(public_key)
        self.client.publish(DISTRIBUTION_TOPIC, str(self.public))
        print(self.name, f' New Key added {str(hash(public_key))[:4]}, reply sent.')

    def _block_callback_ (self, message):
        block = ast.literal_eval(message)
        block = stc.Block(**block)
        self.blockchain.consensus(block)
        pass

    def _transaction_callback_ (self, message):
        pass


@dataclass
class Wallet (Node):
    def __post_init__ (self):
        super().__post_init__()
        self.name = f'[Wallet {str(hash(self.public))[:4]}]'

    def send (self, to, amount):
        transaction = Transaction(self.public, to, self.scheme, amount)
        transaction.sign(self.private)
        print(f'[Node {str(hash(self.public))[:4]}] Sending {amount} to {str(hash(to))[:4]}.')
        self.client.publish(TRANSACTION_TOPIC, str(transaction))

    def random (self):
        time.sleep(5)
        time.sleep(sc.randbelow(3))
        self.send(sc.choice(self.addresses), sc.randbelow(100))

    def rr (self):
        while True:
            self.random()



@dataclass
class Miner (Node):
    def __post_init__ (self):
        super().__post_init__()
        self.client.subscribe(TRANSACTION_TOPIC)
        self.name = f'[Miner {str(hash(self.public))[:4]}]'
        pass
    
    def _transaction_callback_ (self, message):
        print(f'[Node {str(hash(self.public))[:4]}] Recieved new transaction.')
        transaction = Transaction.from_rep(message)
        ledger = self.blockchain.add_to_ledger(transaction)
        if ledger is not None:
            print(f'{self.name} Transaction added to Blockchain.')# \n[ Ledger ]:{ledger}')


    def main (self):
        self.blockchain.start_mining(self._blockchain_callback_)
        pass

    def _blockchain_callback_ (self):
        self.client.publish(BLOCKCHAIN_TOPIC, str(self.blockchain.headers))
        print(f'{self.name} Published: {self.blockchain.headers}')



if __name__ == '__main__':
    e = Miner('D2')
    e.main()
    a = Wallet('D2')
    b = Wallet('D2')
    c = Wallet('D2')
    time.sleep(2)
    d = Wallet('D2')
    a.random()
    b.random()
    c.random()
    d.random()
    tr.Thread(target=a.rr).start()
    time.sleep(20)
