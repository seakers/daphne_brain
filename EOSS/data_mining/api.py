#!/usr/bin/env python
import sys,os

sys.path.append(os.path.dirname(__file__))

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from EOSS.data_mining.interface import DataMiningInterface

from config.loader import ConfigurationLoader
config = ConfigurationLoader().load()

class DataMiningClient():
    def __init__(self):
        port = config['data-mining']['port']

        # Make socket
        self.transport = TSocket.TSocket('localhost', port)
    
        # Buffering is critical. Raw sockets are very slow
        self.transport = TTransport.TBufferedTransport(self.transport)
    
        # Wrap in a protocol
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        
        # Create a client to use the protocol encoder
        self.client = DataMiningInterface.Client(self.protocol)
    
    def startConnection(self):
        # Connect
        self.transport.open()

    def endConnection(self):
        # Close
        self.transport.close()
        
    def ping(self):
        self.client.ping()
        print('ping()')


