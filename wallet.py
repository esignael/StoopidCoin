from transaction import Transaction
import random
import dilithium.dilithium as dl
import falcon.falcon as fl
import paho.mqtt.client as mqtt 
from random import randrange, uniform

class Wallet():
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
            'F1024': fl.Falcon1024,}
    
    mqttBroker ="mqtt.eclipseprojects.io"
    topic = 'simple_coin_wallet_test'

    def __init__(self,scheme_str):
        self.scheme_str = scheme_str
        self.scheme = self.schemes[scheme_str]
        self.pk, self.sk = self.scheme.keygen()
        self.client = mqtt.Client()

    def __str__(self):
        return f'Wallet with scheme: {str(self.scheme_str)}'

    def send_transaction(self, addr_to,amount_sent):
        
        self.client.connect("mqtt.eclipseprojects.io") 

        new_transaction = Transaction(self.pk, addr_to, self.scheme_str, amount_sent)
        new_transaction.sign(self.sk)
        data = vars(new_transaction)
        print(f'Sending {amount_sent} with {self.scheme_str} signature.')
        
        self.client.publish(self.topic, str(data))
        self.client.publish(self.topic, '-----------')

    def send_Ftransaction(self, addr_to, scheme_str_to,amount_sent):
        
        self.client.connect("mqtt.eclipseprojects.io") 

        new_transaction = Transaction(self.pk, addr_to, scheme_str_to, amount_sent)
        new_transaction.sign(self.sk)
        data = vars(new_transaction)
        print(f'Sending {amount_sent} with {scheme_str_to} signature.')
        
        self.client.publish(self.topic, str(data))
        self.client.publish(self.topic, '-----------')


def automated_wallets(schemes_str):
    """
    n: number of random wallets
    """

    n = 0
    wallets = []
    pb_keys = []
    schemes_list = list(schemes_str.keys())

    # Step 1: Create the wallets
    while n < 1:
        n = int(input("""How many wallets? (min 1)\n"""))
    
    for i in range(n):
        scheme = random.choice(schemes_list)
        print(f'Creating {scheme} wallet')
        w = Wallet(scheme)
        wallets.append(w)
        pb_keys.append(w.pk)

    # Step 2: Run transactions 
    tr = int(input("""Number of transtactions:\n """))
    for i in range(tr):
        wallet = random.choice(wallets)
        rnd_scheme = random.choice(schemes_list)
        pb_key = random.choice(pb_keys)
        amount = random.randint(10,100)
        wallet.send_transaction(pb_key,amount)


def manual_wallet(schemes_str):
    response = None
    while response not in ["1", "2", "3", "4"]:
        response = input("""What do you want to do?
        1. Generate new wallet
        2. Send coins to another wallet
        3. Check transactions
        4. Quit\n""")
    if response == "1":
        scheme = None
        while scheme not in ['D2', 'D3', 'D5','F2','F4','F8','F16','F32','F64','F128','F256','F512','F1024','Q']:
            scheme = str(input("""Which scheme you want to use
            D2:     Dilithium2
            D3:     Dilithium3
            D5:     Dilithium5
            F2:     Falcon2
            F4:     Falcon4
            F8:     Falcon8
            F16:    Falcon16
            F32:    Falcon32
            F64:    Falcon64
            F128:   Falcon128
            F256:   Falcon256
            F512:   Falcon512
            F1024:  Falcon1024

            Q:      Quit\n"""))
        if scheme != 'Q':
            w = Wallet(schemes_str[scheme])
            print(F'{w.scheme_str} wallet created\nsk: {w.sk}\npk: {w.pk}')
        else:
            quit()
    # elif response == "2":
    #     addr_from = input("From: introduce your wallet address (public key)\n")
    #     sk = input("Introduce your private key\n")
    #     addr_to = input("To: introduce destination wallet address\n")
    #     amount = input("Amount: number stating how much do you want to send\n")
    #     level = None
    #     while level not in ["1", "2", "3","4"]:
    #         level = input("""Which Dilithium NIST level you want to use
    #         1. Dillithium 2
    #         2. Dillithium 3
    #         3. Dillithium 5
    #         4. Quit\n""")
    #     if level in ["1", "2", "3"]:
    #         dil = {'1': dl.Dilithium2,
    #             '2': dl.Dilithium3,
    #             '3': dl.Dilithium5}   
    #         print("=========================================\n\n")
    #         print("Is everything correct?\n")
    #         lev = {'1': 'D2',
    #             '2': 'D3',
    #             '3': 'D5'}  
    #         print(F"From: {addr_from}\nSecret Key: {sk}\nTo: {addr_to}\nAmount: {amount}\nNIST level: {lev[level]}\n")
    #         response = input("y/n\n")
    #         if response.lower() == "y":
    #             send_transaction(addr_from, sk, addr_to, dil[level], amount)
    #         elif response.lower() == "n":
    #             return wallet() 
    else:
        quit()

    return




if __name__ == '__main__':
    print("""       =========================================\n
        (╯°□°)╯︵ ┻━┻  v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n""")
    schemes_str = {'D2': 'Dilithium2',
            'D3': 'Dilithium3',
            'D5': 'Dilithium5',
            'F2': 'Falcon2',
            'F4': 'Falcon4',
            'F8': 'Falcon8',
            'F16': 'Falcon16',
            'F32': 'Falcon32',
            'F64': 'Falcon64',
            'F128': 'Falcon128',
            'F256': 'Falcon256',
            'F512': 'Falcon512',
            'F1024': 'Falcon1024',}
    automated_wallets(schemes_str)


