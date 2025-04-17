import logging

# Get an instance of a logger
logger = logging.getLogger('config')

import json
from os.path import join, dirname, isfile

DEFAULT_CONFIG = join(dirname(__file__), 'daphne.conf')

class ConfigurationLoader():
    
    def __init__(self):
        self.config = None
    
    def load(self):
        if(self.config):
            return self.config
        else:
            if isfile(DEFAULT_CONFIG):
                try:
                    with open(DEFAULT_CONFIG) as f:
                        self.config = json.load(f)
                except:
                    logger.exception("Exception in loading the configuration file")

            else:
                print("Configuration file not found in {0}".format(DEFAULT_CONFIG))
            return self.config