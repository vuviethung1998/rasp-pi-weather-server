#!/usr/bin/env python

import sys
from sim_module import sim
import time
import json
from sensor_monitoring import dht, wv20,ze12, ze15, ze25, zh03b, INA219 as battery
import board
from datetime import datetime
from time import sleep

def getConfig():
    with open('config/config.json') as config_file:
        config = json.load(config_file)
    return config

def get_body_str(data):
    body = {"records": [{ "key": "sensor_device","value":data}]}
    body_str = json.dumps(body)

    return  body_str

# get kafka rest proxy url
def getURL(config):
    return  'http://' + config['kafka_rest_proxy'] + '/topics/' + config['topic']

def data_sender(config,debug=True):
    # init params
    URL = getURL(config)
    content_type = config['content_type']


    # Init Battery
    Battery = battery.INA219(addr=0x42)

    # init sensor
    # CO2 = wv20.sensor()
    # SO2 = ze12.sensor()
    # CO = ze15.sensor()
    # O3 = ze25.sensor()
    PM2_5 = zh03b.sensor()
    DHT = dht.sensor()

    DHT_PIN = board.D18
    PORT_PM2_5 = '/dev/ttyAMA0'
    # PORT_SO2 = '/dev/ttyAMA1'
    # PORT_CO2 = '/dev/ttyAMA2'
    # PORT_CO = '/dev/ttyAMA3'
    # PORT_O3 = '/dev/ttyAMA4'
    SensorReadMode = 1

    ok_pm25 = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)
    if not ok_pm25:
        print('init PM2.5 error')
        sys.exit(-1)

    ok_dht = DHT.initSensor(DHT_PIN)
    if not ok_dht:
        print('init DHT error')
        sys.exit(-1)

    # init sim
    sim.power_on(config["POWER_KEY"])
    ok = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
    if not ok:
        print('SIM AT init error')
        sys.exit(1)
    # Done init
    main_run = True
    sim.gps_start() # start gps

    # wait till gps get data
    while True:
        gps, ok = sim.gps_get_data()
        if ok is True:
            break
    # loop
    while main_run:
        try:
            time.sleep(2)
            # Get Time
            time_sim = sim.time_get()
            if time_sim != '':
                if debug: print('Time:' + time_sim)

            time.sleep(2)
            # Get GPS
            gps, ok = sim.gps_get_data()
            if ok:
                if debug: print('GPS:' + gps)
            else:
                if debug: print('GPS not ready')

            time.sleep(2)
            # POST HTTP
            # get data
            cur_time =  datetime.now().strftime("%H:%M:%S")
            pm2_5, ok_pm25 = PM2_5.getSensor()
            temp, humid, ok_dht = DHT.getSensor()
            voltage, current, power, percent= Battery.getBusVoltage_V(), Battery.getCurrent_mA(), Battery.getPower_W(), Battery.getPercent()

            if not ok_pm25:
                if debug: print('Error read sensor: PM2.5')
            if not ok_dht:
                if debug: print('Error read sensor: DHT')

            data = {'sleep_time': config['sleep_time'] + 6,'time': cur_time, 'pm2_5_val': pm2_5, 'temp_val': temp, 'humid_val': humid, "voltage": voltage, "current": current, "power": power, "battery_percent": percent}
            body_str = get_body_str(data)
            if debug:
                print('Send data to Server:' + URL)
                print(body_str)
            ok = sim.http_post(URL, content_type, body_str, '', config["HTTP_CONNECT_TIMEOUT"], config["HTTP_RESPONSE_TIMEOUT"])
            if not ok:
                if debug: print('Error send data to Server')
            sleep(config['sleep_time'])

        except KeyboardInterrupt:
            main_run = False
            sim.gps_stop()
            sim.at_close()
            sim.power_down(config["POWER_KEY"])



if __name__=="__main__":
    config = getConfig()
    data_sender(config,debug=True)
