from sim_module.data_sender import getConfig, send_data

if __name__=="__main__":
    config = getConfig()
    send_data(config)
