from sim_module.data_sender import getConfig, send_data
import argparse

if __name__=="__main__":
    debug = False
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        debug = True
    config = getConfig()
    send_data(conf=config,debug=debug)
