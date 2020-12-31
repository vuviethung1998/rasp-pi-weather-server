from confluent_kafka import Consumer, KafkaError
import json
from pymongo import MongoClient, errors
from datetime import datetime
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
                    # check if field createdAt exists
                    # if exist then convert to Date type
                    if 'createdAt' in event.keys():
                        createdAt = event['createdAt'].split('.')[0]
                        event['createdAt'] = datetime.strptime(createdAt, '%H:%M:%S %m-%d-%Y')

                        collection.insert_one(event)
                except TypeError as e:
                    print(e)
                except ValueError as e:
                    print(e)

                msg_count += 1
                if msg_count % config['MIN_COMMIT_COUNT'] == 0:
                    kafka_consumer.commit()
        finally:
            kafka_consumer.close()
    except errors.ServerSelectionTimeoutError as err:
        # do whatever you need
        print(err)

    # curl -X POST -d {{"records": [{ "key": "sensor_device","value": "{'pm2_5_val': 0, 'temp_val': 0, 'humid_val': 0}" }]}} -H "Content-Type: application/vnd.kafka.json.v2+json" http://157.230.32.117:8082/topics/test-pi




