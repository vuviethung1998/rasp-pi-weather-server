from confluent_kafka import Producer, Consumer, KafkaError
import json
from sense_hat import SenseHat
from time import sleep
import datetime

def getConfig():
    with open('../config/config.json') as config_file:
        config = json.load(config_file)
    return config

def getTempHumidTime():
    temp = sense.get_temperature()
    humidity = sense.get_humidity()
    # ct stores current time
    ct = datetime.datetime.now()

    # ts store timestamp of current time
    ts = ct.timestamp()

    return temp, humidity, ts


if __name__=="__main__":
    sense = SenseHat()
    config = getConfig()

    kafka_consumer = Consumer({
        'bootstrap.servers': config['bootstrap_servers'],
        'group.id': config['group_id'],
        'default.topic.config': {
            'auto.offset.reset': config['offset']
        }
    })

    kafka_producer = Producer({
        'bootstrap.servers': config['bootstrap_servers']
        # 'bootstrap.servers': ["10.10.137.42:6667", "10.10.137.43:6667"]
    })
    # kafka_consumer.subscribe(['snowplow_enriched_good'])


    while True:
        try:
            json_data = getTempHumidTime()
            kafka_producer.poll(0)
            kafka_producer.produce(config['topic'], json.dumps(json_data).encode('utf-8'))
            kafka_producer.flush()
            sleep(3)
        except KeyboardInterrupt:
            sense.clear()
            sleep(3)