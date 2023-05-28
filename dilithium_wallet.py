from transaction import Transaction
import requests
import dilithium.dilithium as dl
import json
import base64



""" 
#and then whenever a transactions happens,

new_transaction = Transaction(your_pk, other_pk, 'F2', amount_sent)
new_transaction.sign(your_sk)
# which creates and signs the transaction, then you can use the vars function to get the dict rep of the object
for_json = vars(new_transaction)
# then do the json dump or whatever thing
"""


def wallet():
    response = None
    while response not in ["1", "2", "3", "4"]:
        response = input("""What do you want to do?
        1. Generate new wallet
        2. Send coins to another wallet
        3. Check transactions
        4. Quit\n""")
    if response == "1":
        level = None
        while level not in ["1", "2", "3","4"]:
            level = input("""Which Dilithium NIST level you want to use
            1. Dillithium 2
            2. Dillithium 3
            3. Dillithium 5
            4. Quit\n""")
        if level in ["1", "2", "3"]:
            dil = {'1': dl.Dilithium2,
                '2': dl.Dilithium3,
                '3': dl.Dilithium5}   
            keys_generate(dil[level])
        if level == 4:
            quit()
    elif response == "2":
        addr_from = input("From: introduce your wallet address (public key)\n")
        sk = input("Introduce your private key\n")
        addr_to = input("To: introduce destination wallet address\n")
        amount = input("Amount: number stating how much do you want to send\n")
        level = None
        while level not in ["1", "2", "3","4"]:
            level = input("""Which Dilithium NIST level you want to use
            1. Dillithium 2
            2. Dillithium 3
            3. Dillithium 5
            4. Quit\n""")
        if level in ["1", "2", "3"]:
            dil = {'1': dl.Dilithium2,
                '2': dl.Dilithium3,
                '3': dl.Dilithium5}   
            print("=========================================\n\n")
            print("Is everything correct?\n")
            lev = {'1': 'D2',
                '2': 'D3',
                '3': 'D5'}  
            print(F"From: {addr_from}\nSecret Key: {sk}\nTo: {addr_to}\nAmount: {amount}\nNIST level: {lev[level]}\n")
            response = input("y/n\n")
            if response.lower() == "y":
                send_transaction(addr_from, sk, addr_to, dil[level], amount)
            elif response.lower() == "n":
                return wallet() 
            
        if level == 4:
            quit()
        # return to main menu
    # elif response == "3":  # Will always occur when response == 3.
    #     check_transactions()
    #     return wallet()  # return to main menu
    else:
        quit()

    return

def send_transaction(addr_from, my_sk, addr_to, level, amount_sent):
    new_transaction = Transaction(addr_from, addr_to, level, amount_sent)
    new_transaction.sign(my_sk)
    data = vars(new_transaction)
    print(data)

    url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, data=json.dumps(data), headers=headers)
    print(r.text)
    return

def keys_generate(level):
    raw_pk,raw_sk = level.keygen()

    pk = base64.b64encode(bytes.fromhex(raw_pk.hex()))
    sk = raw_sk.hex()
    filename = input("name of the file in which the address and secret key will be saved as txt file: ") + ".txt"
    with open(filename, "w") as f:
        f.write(F"Wallet address: {pk}\nPrivate key: {sk}")
    print(F"Address and private key saved in {filename}")



if __name__ == '__main__':
    wallet()


