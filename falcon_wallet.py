
import requests
import time
import base64
import json
from transaction import Transaction
import falcon.falcon as fl


def wallet():
    response = None
    while response not in ["1", "2", "3", "4"]:
        response = input("""What do you want to do?
        1. Generate new wallet
        2. Send coins to another wallet
        3. Check transactions
        4. Quit\n""")
    if response == "1":
        # Generate new wallet
        print("""=========================================\n
IMPORTANT: save this credentials or you won't be able to recover your wallet\n
=========================================\n""")
        # f_version = None
        # while f_version not in ["2", "4", "8", "16","32", "64","128", "256","512", "1024"]:
        #    f_version = input("""What version of falcon do you want to use? 2, 4, 8...., 1024\n""")
        #    generate_falcon_keys(f_version)
        generate_falcon_keys(512)
    elif response == "2":
        file_path = input("Introduce your file\n")
        other_pk = input("To: introduce destination wallet address\n")
        amount_sent = input("Amount: number stating how much do you want to send\n")
        with open(file_path, 'r') as file:
            lines = file.readlines()
        your_sk = ''.join(lines[2:6])
        your_pk = ''.join(lines[9:10])
        print(your_sk, your_pk)
        print("=========================================\n\n")
        print("Is everything correct?\n")
        print(F"From: {your_pk}\nPrivate Key: {your_sk}\nTo: {other_pk}\nAmount: {amount_sent}\n")
        response = input("y/n\n")
        if response.lower() == "y":
            Transaction(your_pk, other_pk, 'F2', amount_sent)
        elif response.lower() == "n":
            return wallet()  # return to main menu
    elif response == "3":  # Will always occur when response == 3.
        check_transactions()
        return wallet()  # return to main menu
    else:
        quit()


def check_transactions():
    """Retrieve the entire blockchain. With this you can check your
    wallets balance. If the blockchain is to long, it may take some time to load.
    """
    try:
        res = requests.get('http://localhost:5000/blocks')
        parsed = json.loads(res.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))
    except requests.ConnectionError:
        print('Connection error. Make sure that you have run miner.py in another terminal.')


def generate_falcon_keys(m):
    private_key = fl.SecretKey(m)
    public_key = fl.PublicKey(private_key)

    filename = input("Write the name of your new address: ") + ".txt"
    with open(filename, "w") as f:
        f.write(F"Private key: {private_key.__repr__()}\nWallet address / Public key: {public_key.__repr__()}")
    print(F"Your new address and private key are now in the file {filename}")



if __name__ == '__main__':
    print("""       =========================================\n
        STOOPIDCOIN - falcon (╯°□°)╯︵ ┻━┻  v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        \n""")
    wallet()
    input("Press ENTER to exit...")
