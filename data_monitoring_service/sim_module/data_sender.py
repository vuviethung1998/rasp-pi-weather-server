#!/usr/bin/env python

import sys
from sim_module import sim
import time
import json
from sensor_monitoring import dht, wv20,ze12, ze15, ze25, zh03b, INA219 as battery
import board
from datetime import datetime, time as mytime
from time import sleep
import logging
from logging.handlers import RotatingFileHandler


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def getConfig(confile):
    with open(confile) as config_file:
        config = json.load(config_file)
    return config

def get_body_str(data):
    body = {"records": [{ "key": "sensor_device","value":data}]}
    body_str = json.dumps(body,indent=4, sort_keys=True, default=str) # if not serialisable, default stringify
    
    return  body_str

# get kafka rest proxy url
def getURL(config):
    return  'http://' + config['kafka_rest_proxy'] + '/topics/' + config['topic']


# if time exceeds time limit then restart device
def restartSim(config,debug=True):
    stopSim(config)
    startSim(config,debug)
    
    
def startSim(config, debug=True):
    sim.power_on(config["POWER_KEY"])
    ok_sim = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
    sim.gps_start() # start gps
    

def stopSim(config):
    sim.gps_stop()
    sim.at_close()
    sim.power_down(config["POWER_KEY"])

# send data to server
def data_sender(config,debug=True):
    # create logger with 'spam_application'
    logging.basicConfig(filename='./debug.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

    logging.info("Running Urban Planning")
    logger = logging.getLogger('urbanGUI')


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
    PORT_PM2_5 = '/dev/ttyAMA1'
    # PORT_SO2 = '/dev/ttyAMA1'
    # PORT_CO2 = '/dev/ttyAMA2'
    # PORT_CO = '/dev/ttyAMA3'
    # PORT_O3 = '/dev/ttyAMA4'
    SensorReadMode = 1

    # # init state of devices
    # state = initState()
    # init sensor
    ok_pm25 = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)
    ok_dht = DHT.initSensor(DHT_PIN)
    # init sim
    sim.power_on(config["POWER_KEY"])
    ok_sim = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
    # init gps
    sim.gps_start() # start gps
    gps, ok_gps = sim.gps_get_data()

    # Wait till turn gps on, if over 3 mins move on 
    time_limit = time.time() + 3 * 60
    while not ok_gps:
        _, ok_gps = sim.gps_get_data()
        if time.time() > time_limit:
            break
    logger.info('All devices are on.')

    # Done init
    main_run = True

    # loop
    while main_run:
        try:
            gps, ok_gps = sim.gps_get_data()
            if ok_gps:
                lst_str = gps.split(',') # split GPS string2
                lat, ns, lon, ew, _, _, altitude, speed, _ = float(lst_str[0].strip()) /100, lst_str[1].strip(), float(lst_str[2].strip()) /100, lst_str[3].strip(), lst_str[4].strip(), lst_str[5].strip(), lst_str[6].strip(), lst_str[7].strip(), lst_str[8].strip()
            else:
                logger.error('GPS failed')
                lat, ns, lon, ew, _, _, altitude, speed, _ = '','','','','','','','',''


            # Get time data
            cur_time =  datetime.now().strftime("%H:%M:%S")
            cur_date =  datetime.now().strftime("%m-%d-%Y")
            created_at = datetime.now().strftime("%H:%M:%S %m-%d-%Y")
            
            # if between 0 and 1 am -> convert to 00
            if is_time_between(mytime(0,0), mytime(1,0)):
                lst_min_sec = cur_time.split(':')[1:]
                cur_time = '00:' + ':'.join(lst_min_sec)
                created_at = cur_time + ' ' + cur_date


            
            # Get temp humid
            temp, humid, ok_dht = DHT.getSensor()
            print(type(temp))
            time_limit_dht = time.time() + 60  #  from now

            while not ok_dht or temp == 0 or humid == 0:
                logger.error('dht failed')
                temp, humid, ok_dht = DHT.getSensor()
                if time.time() > time_limit_dht:
                    DHT = dht.sensor()
                    ok_dht= DHT.initSensor(DHT_PIN)
                    temp, humid, ok_dht = DHT.getSensor()

            # Get PM2.5 data
            pm2_5, ok_pm25 = PM2_5.getSensor()
            time_limit_pm25 = time.time() + 60   #  from now
            while not ok_pm25 or pm2_5 == 0:
                logger.error('pm2.5 failed')
                pm2_5, ok_pm25 = PM2_5.getSensor()
                if time.time() > time_limit_pm25:
                    PM2_5 = zh03b.sensor()
                    ok_pm25 = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)                  
                    pm2_5, ok_pm25 = PM2_5.getSensor()

            # Get battery data
            voltage, current, power, percent= Battery.getBusVoltage_V(), Battery.getCurrent_mA(), Battery.getPower_W(), Battery.getPercent()

            # get data
            data = {'sleep_time': config['sleep_time'], 'createdAt': created_at, 'date': cur_date, 'time': cur_time, 'lat':lat, 'lon':lon, 'ns':ns, 'ew': ew, 'altitude': altitude, 'speed': speed, 'pm2_5_val': pm2_5, 'temp_val': temp, 'humid_val': humid, "voltage": voltage, "current": current, "power": power, "battery_percent": percent }
            body_str = get_body_str(data)
            if debug:
                logger.info('Send data to Server:' + URL)
                logger.info('Body string: '+ body_str)
            ok_post = sim.http_post(URL, content_type, body_str, '', config["HTTP_CONNECT_TIMEOUT"], config["HTTP_RESPONSE_TIMEOUT"])
            
            time_limit_post = time.time() + 3* 60
            while not ok_post:
                if debug: logger.error('Error send data to Server')
                ok_sim = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
                ok_post = sim.http_post(URL, content_type, body_str, '', config["HTTP_CONNECT_TIMEOUT"], config["HTTP_RESPONSE_TIMEOUT"])

                if time.time() > time_limit_post:
                    if debug: logger.error('Error send data to Server. Restarting SIM')
                    restartSim(config)
                    time_limit_post = time.time() + 3 * 60
            sleep(config['sleep_time'])

        except KeyboardInterrupt:
            main_run = False
            stopSim(config)

if __name__=="__main__":
    config = getConfig()
    data_sender(config,debug=True)
