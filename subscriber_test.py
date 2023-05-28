import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, message):
    print("received message: " ,str(message.payload.decode("utf-8")))

    
mqttBroker ="mqtt.eclipseprojects.io"
topic = 'simple_coin_wallet_test'

client = mqtt.Client("Miner")
client.connect(mqttBroker) 

while True:
    client.loop_start()

    client.subscribe(topic)
    client.on_message=on_message 

    time.sleep(30)
    client.loop_stop()