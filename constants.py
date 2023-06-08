import dilithium.dilithium as dl
import falcon.falcon as fl


INIT_NONCE = 210644719005073877671183486889312693096397064091025351375451711930375496953659526255563761750541064217744541030831433544377227285704512570076943590210700
INIT_CHALLENGE = 17
BROKER = 'test.mosquitto.org'
BROKER = '127.0.0.1'
PORT = 1883
MAIN_TOPIC = 'stoopid_coin'
DISTRIBUTION_TOPIC = MAIN_TOPIC + '/key_distribution'
TRANSACTION_TOPIC = MAIN_TOPIC + '/transactions'
BLOCKCHAIN_TOPIC = MAIN_TOPIC + '/blockchain'
RECEIPT_TOPIC = MAIN_TOPIC + '/receipt/response'
REQUEST_TOPIC = MAIN_TOPIC + '/receipt/request'
KILL = MAIN_TOPIC + '/kill'
REWARD = 4.2
BACKEND = { 'D2': dl.Dilithium2,
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
