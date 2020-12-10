import sys
from  sim_module import sim
import time
import json
from sensor_monitoring import humidity, temperature
from sensor_monitoring.dust import set_up_GPIO, read
from sense_hat import SenseHat
from time import sleep

def getConfig():
    with open('config/config.json') as config_file:
        config = json.load(config_file)
    return config

def get_body_str(data):
    body = {"records": [data]}
    body_str = json.dumps(body)
    return  body_str

# get kafka rest proxy url
def getURL(config):
    return  'http://' + config['kafka_rest_proxy'] + '/topics/' + config['topic']

def data_sender(data,config,debug=True):
    # init params
    URL = getURL(config)
    content_type = config['content_type']
    body_str = get_body_str(data)
    # init sim
    sim.power_on(config["POWER_KEY"])
    sim.gps_start() # start gps
    ok = sim.at_init(config["SIM_SERIAL_PORT"], config["SIM_SERIAL_BAUD"])
    if not ok:
        print('SIM AT init error')
        sys.exit(1)
    # Done init
    main_run = True
    # loop
    try:
        while main_run:
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
            if debug:
                print('Send data to Server:' + URL)
                print(body_str)
            ok = sim.http_post(URL, content_type, body_str, '',config["HTTP_CONNECT_TIMEOUT"], config["HTTP_RESPONSE_TIMEOUT"])
            if not ok:
                if debug: print('Error send data to Server')

    except KeyboardInterrupt:
        # main_run = False
        sim.gps_stop()
        sim.at_close()
        sim.power_down(config["POWER_KEY"])

def send_data(conf):
    set_up_GPIO()
    while True:
        dust = read()
        temp = temperature.temperature()
        humid = humidity.humidity()

        data = {'dust_val': dust, 'temp_val': temp, 'humid_val': humid}
        data_sender(data=data, config=conf)
        sleep(5)

if __name__=="__main__":
    config = getConfig()
    send_data(config)
