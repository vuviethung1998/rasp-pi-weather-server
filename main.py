from sim_module.data_sender import getConfig, data_sender
import argparse

if __name__=="__main__":
    debug = False
    parser = argparse.ArgumentParser()
    parser.add_argument("-debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        debug = True
    config = getConfig()
    data_sender(config=config,debug=debug)
