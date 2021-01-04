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
    body_str = json.dumps(body,indent=4, sort_keys=True, default=str) # if not serialisable, default stringify
    
    return  body_str

# get kafka rest proxy url
def getURL(config):
    return  'http://' + config['kafka_rest_proxy'] + '/topics/' + config['topic']

def initState():
    state = {}
    state['dht'] = False
    state['pm25'] = False
    state['gps'] = False
    state['sim'] = False
    return state

def checkAllSensorSucceed(state):
    if state['dht'] != True or state['pm25'] != True or state['gps'] != True  or state['sim'] != True:
        return False
    return True

# if time exceeds timelimit or device result passed, return True
def reTryUntilGetData(timelimit, device_ok):
    if device_ok or time.time() > timelimit:
        return True
    return False

# if time exceeds timelimit, restart sim
def reTryUntilGetGPSData(timelimit, device_ok, config, debug):
    if device_ok:
        return True
    elif not device_ok and time.time() > timelimit:
        restartSim(config, debug)
        return False
    return False

# if time exceeds time limit then restart device
def restartSim(config, debug):
    startSim(config, debug)
    stopSim(config)
    
def startSim(config, debug):
    sim.power_on(config["POWER_KEY"])
    ok_sim = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
    sim.gps_start() # start gps
    

def stopSim(config):
    sim.gps_stop()
    sim.at_close()
    sim.power_down(config["POWER_KEY"])

# send data to server
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

    # init state of devices
    state = initState()
    # init sensor
    #ok_pm25 = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)
    #ok_dht= DHT.initSensor(DHT_PIN)
    # init sim
    #sim.power_on(config["POWER_KEY"])
    #ok_sim = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
    # init gps
    #sim.gps_start() # start gps
    #gps, ok_gps = sim.gps_get_data()
    
    # init sim
    startSim(config,debug)

    # define state
    #state['dht'], state['pm25'], state['gps'], state['sim'] = ok_dht, ok_pm25, ok_gps, ok_sim

    # if device cannot start within limit range then restart sim 
    time_limit_all_devices = time.time() + 2 * 60   # 120s from now
    while not checkAllSensorSucceed(state):
        ok_pm25 = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)
        ok_dht= DHT.initSensor(DHT_PIN)
        ok_sim = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"], debug)
        _, ok_gps = sim.gps_get_data()
        state['dht'], state['pm25'], state['sim'], state['gps'] = ok_dht, ok_pm25, ok_sim, ok_gps

        if not checkAllSensorSucceed(state) and time.time() > time_limit_all_devices: 
            restartSim(config, debug)
            time_limit_all_devices  = time.time() + 2 * 60         
    print('All devices are on.')

    # Done init
    main_run = True

    # loop
    while main_run:
        try:
            # time_sim = sim.time_get()
            # Get GPS data
            time_limit_gps = time.time() + 10   #  from now
            while True:
                gps, _ = sim.gps_get_data()
                if gps == '' or gps is None:
                    state_gps = False
                else:
                    state_gps =  True
                state_data = reTryUntilGetGPSData(timelimit=time_limit_gps, device_ok=state_gps, config, debug) # check data passed
                if state_data:
                    break
            lst_str = gps.split(',') # split GPS string2
            lat, ns, lon, ew, _, _, altitude, speed, _ = float(lst_str[0].strip()) /100, lst_str[1].strip(), float(lst_str[2].strip()) /100, lst_str[3].strip(), lst_str[4].strip(), lst_str[5].strip(), lst_str[6].strip(), lst_str[7].strip(), lst_str[8].strip()

            # Get time data
            cur_time =  datetime.now().strftime("%H:%M:%S")
            cur_date =  datetime.now().strftime("%m-%d-%Y")
            created_at = datetime.now().strftime("%H:%M:%S %m-%d-%Y")

            # Get temp humid
            time_limit_dht = time.time() + 10   #  from now
            while True:
                temp, humid, _ = DHT.getSensor()
                if temp == 0 or humid == 0 or temp is None or humid is None:
                    state_dht = False
                else:
                    state_dht =  True
                state_data = reTryUntilGetData(timelimit=time_limit_dht, device_ok=state_dht) # check data passed
                if state_data:
                    break

            # Get PM2.5 data
            time_limit_pm25 = time.time() + 10   #  from now
            while True:
                pm2_5, _ = PM2_5.getSensor()
                if pm2_5 == 0 or pm2_5 is None:
                    state_pm25 = False
                else:
                    state_pm25 = True
                state_data = reTryUntilGetData(timelimit=time_limit_pm25, device_ok=state_pm25) # check data passed

                if state_data:
                    break

            # Get battery data
            voltage, current, power, percent= Battery.getBusVoltage_V(), Battery.getCurrent_mA(), Battery.getPower_W(), Battery.getPercent()

            # get data
            data = {'sleep_time': config['sleep_time'] + 6, 'createdAt': created_at, 'date': cur_date, 'time': cur_time, 'lat':lat, 'lon':lon, 'ns':ns, 'ew': ew, 'altitude': altitude, 'speed': speed, 'pm2_5_val': pm2_5, 'temp_val': temp, 'humid_val': humid, "voltage": voltage, "current": current, "power": power, "battery_percent": percent }
            body_str = get_body_str(data)
            if debug:
                print('Send data to Server:' + URL)
                print(body_str)
            ok_post = sim.http_post(URL, content_type, body_str, '', config["HTTP_CONNECT_TIMEOUT"], config["HTTP_RESPONSE_TIMEOUT"])
            if not ok_post:
                if debug: print('Error send data to Server')
            sleep(config['sleep_time'])

        except KeyboardInterrupt:
            main_run = False
            stopSim(config)



if __name__=="__main__":
    config = getConfig()
    data_sender(config,debug=True)
