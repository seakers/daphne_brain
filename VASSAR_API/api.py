#!/usr/bin/env python

#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#

import sys
import glob

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from VASSAR_API.interface import interface as VASSARInterface


from config.loader import ConfigurationLoader
config = ConfigurationLoader().load()



class VASSARClient():
    
    def __init__(self):
        
        port = config['vassar']['port']
        
        # Make socket
        self.transport = TSocket.TSocket('localhost', port)
    
        # Buffering is critical. Raw sockets are very slow
        self.transport = TTransport.TBufferedTransport(self.transport)
    
        # Wrap in a protocol
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        
        # Create a client to use the protocol encoder
        self.client = VASSARInterface.Client(self.protocol)
        
    
    def startConnection(self):
        # Connect
        self.transport.open()

    
    def endConnection(self):
        # Close
        self.transport.close()
        
    def initializeJess(self):
        message = self.client.initJess()
        print(message)
        return message
    
    def evaluateArchitecture(self):
        arch_formatted = self.client.eval('')
        arch = {'science':arch_formatted.science,'cost':arch_formatted.cost,'booleanString':arch_formatted.booleanString}
        print('Test arch evaluated. Science: {0}, Cost: {1}'.format(arch['science'], arch['cost']))
        return arch
        
    def ping(self):
        self.client.ping()
        print('ping()')
        
    def getOrbitList(self):
        return self.client.getOrbitList()
    
    def getInstrumentList(self):
        return self.client.getInstrumentList()

    

if __name__ == '__main__':
    try:
        #main()
        pass
    except Thrift.TException as tx:
        print('%s' % tx.message)
