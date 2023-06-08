import time
import secrets as st
import queue as qu
import pdb
from constants import *
from dataclasses import dataclass
import threading as tr
import StoopidCoin as stc
import paho.mqtt.client as mqtt
import ast
import json 
import logging
import secrets as sc


@dataclass
class Node ():
    scheme: str = None
    def __post_init__ (self):
        if self.scheme is None:
            self.scheme = st.choice(list(BACKEND.keys()))
        self.public, self.private = BACKEND[self.scheme].keygen()
        self.exploit = BACKEND[self.scheme].keygen()
        self.name = str(hash(str(self.public)))[10:]
        self.__init_logger__()
        self.logger.info(f'[ INIT ] {self.scheme}\n=== Public Key ===\n{self.public}\n{"=" * 17}')
        self.logger.info(f'=== Private Key ===\n{self.private}\n{"=" * 18}')
        self.addresses = []
        self.__init_client__()
        self.client.subscribe(DISTRIBUTION_TOPIC)
        self.client.subscribe(BLOCKCHAIN_TOPIC)
        self.client.subscribe(KILL)
        self.client.publish(DISTRIBUTION_TOPIC, str(self.public))
        self.blockchain = stc.BlockChain()
        self.chain_lock = tr.Lock()
        self.stop = False

    def __init_logger__ (self):
        self.logger = logging.getLogger(str(self.public))
        file_handler = logging.FileHandler(f'logs/{self.name}.log', mode='w+')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def __init_client__ (self):
        self.client = mqtt.Client()
        self.client.on_message = self.__on_message__
        self.client.connect(BROKER, PORT)
        self.client.loop_start()

    def __on_message__ (self, client, userdata, package):
        message = package.payload.decode()
        self.logger.info(f'{"-"*20}\n[ INFO ] [ <<< {package.topic} ] Message recieved. ')
        if package.topic == DISTRIBUTION_TOPIC:
            self.__distribution_callback__(message)
        elif package.topic == TRANSACTION_TOPIC:
            self._transaction_callback_(message)
        elif package.topic == BLOCKCHAIN_TOPIC:
            self._new_block_callback_(message)
        elif package.topic == KILL:
            self._kill_()

    def __distribution_callback__ (self, message):
        public_key = ast.literal_eval(message)
        if public_key in self.addresses:
            return
        if public_key == self.public:
            return
        self.addresses.append(public_key)
        self.logger.info(f'[ INFO ] [ New key added into known keys. ]\n{public_key}')
        self.client.publish(DISTRIBUTION_TOPIC, str(self.public))
        self.logger.info(f'[ INFO ] [ >>> {DISTRIBUTION_TOPIC} ] [ Key published for the new node. ]')

    def _new_block_callback_ (self, message):
        new_headers = ast.literal_eval(message)
        new_chain = [stc.Header(**header) for header in new_headers]
        self.chain_lock.acquire()
        try:
            self._consensus_(new_chain)
        finally:
            self.chain_lock.release()

    def _consensus_ (self, new_chain):
        if len(new_chain) <= len(self.blockchain.headers):
            return
        for header in self.blockchain.headers[::-1]:
            if header in new_chain:
                break
        index = header.index
        self.blockchain.headers[index:] = new_chain[index:]
        self.blockchain.ledgers[index:] = [None] * len(new_chain[index:])
        self._clear_ledger_()
        self.logger.info(f'[ INFO ] [ New block has been accepted into the chain. ]\n{new_chain}')
        self.logger.info(new_chain)

    def _clear_ledger_ (self):
        pass

    def _transaction_callback_ (self, message):
        pass

    def _kill_ (self):
        self.stop = True

    def kill (self):
        self.client.publish(KILL, 1)

@dataclass
class Wallet (Node):
    def send (self, to, amount):
        transaction = stc.Transaction(self.public, to, self.scheme, amount)
        transaction.sign(self.private)
        print(f'[Node {self.name}] Sending {amount} to {str(hash(str(to)))[:4]}.')
        self.client.publish(TRANSACTION_TOPIC, str(transaction))
        info = f'{"-"*20}\n[ INFO ] [ >>> {TRANSACTION_TOPIC} ] [ New transaction published. ]'
        self.logger.info(info)
        self.logger.info(f'{transaction}\n{"-"*20}')
        print(info)

    def wrong_sig (self, to, amount):
        public, private = self.exploit
        transaction = stc.Transaction(self.public, to, self.scheme, amount)
        transaction.sign(private)
        transaction.sender = public
        self.client.publish(TRANSACTION_TOPIC, str(transaction))
        info = f'{"-"*20}\n[ INFO ] [ >>> {TRANSACTION_TOPIC} ] [ Exploitative transaction published. ]'
        self.logger.info(info)
        self.logger.info(f'{transaction}\n{"-"*20}')
        print(info)

    def random (self):
        to, amount = sc.choice(self.addresses), sc.randbelow(100)
        st.choice([self.send, self.wrong_sig])(to, amount)

    def rr (self):
        while not self.stop:
            self.random()
            time.sleep(st.randbelow(60) / 20)

    def manual (self):
        while True:
            pass


@dataclass
class Miner (Node):
    def __post_init__ (self):
        super().__post_init__()
        self.client.subscribe(TRANSACTION_TOPIC)
        self.client.subscribe(REQUEST_TOPIC)
        self.check = tr.Event()
        self.ledger = qu.Queue()
        self.ledger.put(self._new_ledger_())

    def _clear_ledger_ (self):
        self.ledger.get()
        self.ledger.put(self._new_ledger_())

    def _new_ledger_ (self):
        reward = stc.Transaction(self.public, 'Reward', self.scheme, REWARD)
        reward.sign(self.private)
        return stc.Merkle([reward.digest()])
    
    def _transaction_callback_ (self, message):
        print(f'[ {self.name} ] Recieved new transaction.')
        transaction = stc.Transaction.from_rep(message)
        self.check.clear()
        try:
            ledger = self._add_to_ledger_(transaction)
        finally:
            self.check.set()
        if ledger is not None:
            print(f'{self.name} Transaction added to Blockchain.')# \n[ Ledger ]:{ledger}')
            self.logger.info(f'[ INFO ] [ New transaction added to the ledger. ]\n{str(ledger.intdigests)}')

    def _add_to_ledger_ (self, transaction):
        if not transaction.verify():
            self.logger.info(f'[ WARNING ] [ Transaction with wrong signature! ]')
            return None
        ledger = self.ledger.get()
        ledger.append(transaction.digest())
        self.ledger.put(ledger)
        return ledger

    def start_mining (self):
        thread = tr.Thread(target=self._start_mining)
        thread.start()

    def _start_mining (self):
        while not self.stop:
            self.chain_lock.acquire()
            try:
                self.check.wait()
                self._new_header_()
            finally:
                self.chain_lock.release()

    def _new_header_ (self):
        ledger = self.ledger.get()
        try:
            prev_hash = self.blockchain.headers[-1].intdigest()
            index = self.blockchain.headers[-1].index
            nonce = st.randbelow(1 << 512)
            new_header = stc.Header(index=index+1, prev_block=prev_hash, nonce=nonce, merkle_root=ledger.intdigest())
            if not new_header.is_proven():
                return
            self.blockchain.append(new_header, ledger)
            self._blockchain_callback_()
            ledger = self._new_ledger_()
        finally:
            self.ledger.put(ledger)


    def _blockchain_callback_ (self):
        headers = [vars(header) for header in self.blockchain.headers]
        self.client.publish(BLOCKCHAIN_TOPIC, str(headers))
        print(f'{self.name} Published: {self.blockchain.headers}')


if __name__ == '__main__':
    e = Miner()
    d = Miner()
    a = Wallet()
    b = Wallet()
    time.sleep(1)
    e.start_mining()
    d.start_mining()
    tr.Thread(target=a.rr).start()
    tr.Thread(target=b.rr).start()
    time.sleep(60)
    a.kill()
