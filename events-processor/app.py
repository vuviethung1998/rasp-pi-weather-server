from confluent_kafka import Consumer, KafkaError
import json
from pymongo import MongoClient, errors

def getConfig():
    with open('./config.json') as config_file:
        config = json.load(config_file)
    return config

if __name__=="__main__":
    config = getConfig()
    try:
        connection = MongoClient(config['MONGODB_URI'])
        connection.server_info()
        db = connection[config['MONGODB_DATABASE']]
        collection = db.database[config['CRAWLER_COLLECTION']]

        kafka_consumer = Consumer({
            'bootstrap.servers': config['bootstrap_servers'],
            'group.id': config['group_id'],
            'default.topic.config': {
                'auto.offset.reset': config['offset']
            }
        })

        kafka_consumer.subscribe(['test-pi'])
        try:
            msg_count = 0
            while True:
                msg = kafka_consumer.poll(1.0)
                if msg is None: continue
                elif msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print("kafka error: " + str(msg.error()))
                        break
                try:
                    event = dict(json.loads(msg.value().decode('utf-8')))
                    collection.insert_one(event)
                except TypeError as e:
                    print(e)
                msg_count += 1
                if msg_count % config['MIN_COMMIT_COUNT'] == 0:
                    kafka_consumer.commit()
        finally:
            kafka_consumer.close()
    except errors.ServerSelectionTimeoutError as err:
        # do whatever you need
        print(err)



