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

        # # Make socket
        # self.transport = TSocket.TSocket(os.environ['DATAMINING_HOST'], os.environ['DATAMINING_PORT'])
        #
        # # Buffering is critical. Raw sockets are very slow
        # self.transport = TTransport.TBufferedTransport(self.transport)
        self.transport = None
    
        # Wrap in a protocol
        # self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.protocol = None
        
        # Create a client to use the protocol encoder
        # self.client = DataMiningInterface.Client(self.protocol)
        self.client = None
    
    def startConnection(self):
        print('--> DATAMINING (PLACEHOLDER): startConnection')
        # # Connect
        # self.transport.open()

    def endConnection(self):
        print('--> DATAMINING (PLACEHOLDER): endConnection')
        # # Close
        # self.transport.close()
        
    def ping(self):
        print('--> DATAMINING (PLACEHOLDER): ping')
        # self.client.ping()
        # print('ping()')


