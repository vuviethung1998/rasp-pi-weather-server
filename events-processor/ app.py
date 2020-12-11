from confluent_kafka import Producer, Consumer, KafkaError
import snowplow_analytics_sdk.event_transformer
import snowplow_analytics_sdk.snowplow_event_transformation_exception
import json
from pymongo import MongoClient

def getConfig():
    with open('./config.json') as config_file:
        config = json.load(config_file)
    return config


if __name__=="__main__":

    config = getConfig()

    connection = MongoClient(config['MONGODB_URI'])
    db = connection[config['MONGODB_DATABASE']]
    collection = db.database[config['CRAWLER_COLLECTION']]

    kafka_consumer = Consumer({
        'bootstrap.servers': config['bootstrap_servers'],
        'group.id': config['group_id'],
        'default.topic.config': {
            'auto.offset.reset': config['offset']
        }
    })

    # kafka_producer = Producer({
    #     'bootstrap.servers': config['bootstrap_servers']
    #     # 'bootstrap.servers': ["10.10.137.42:6667", "10.10.137.43:6667"]
    # })
    kafka_consumer.subscribe(['test-pi'])

    while True:
        msg = kafka_consumer.poll(1.0)

        if msg is None:
            continue
        elif msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF: continue
            else:
                print("kafka error: " + msg.error())
                break

        event = msg.value().decode('utf-8')
        print(event)
        try:
            json_data = snowplow_analytics_sdk.event_transformer.transform(event)
            print(json_data)
            collection.insert(dict(json_data))

        except snowplow_analytics_sdk.snowplow_event_transformation_exception.SnowplowEventTransformationException as e:
            for error_message in e.error_messages:
                print("kafka error: " + error_message)