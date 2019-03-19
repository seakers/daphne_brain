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

import os,sys
import glob

sys.path.append(os.path.dirname(__file__))

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from VASSAR_API.thriftinterface import VASSARInterface


from config.loader import ConfigurationLoader
config = ConfigurationLoader().load()



class VASSARClient():
    
    def __init__(self, port=9090):
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
    
    def evaluateArchitecture(self, problem, bitString):
        assignation_problems = ['SMAP', 'SMAP_JPL1', 'SMAP_JPL2', 'ClimateCentric']
        partition_problems = ['Decadal2017Aerosols']
        if problem in assignation_problems:
            arch_formatted = self.client.evalBinaryInputArch(problem, bitString)
        elif problem in partition_problems:
            arch_formatted = self.client.evalDiscreteInputArch(problem, bitString)
        else:
            raise Exception('Problem not recognized')
        arch = { 'id': arch_formatted.id, 'inputs': arch_formatted.inputs, 'outputs': arch_formatted.outputs }
        return arch
    
    def runLocalSearch(self, bitString):
        archs_formatted = self.client.runLocalSearch(bitString)
        archs = []
        for arch_formatted in archs_formatted:
            arch = { 'id': arch_formatted.id, 'inputs': arch_formatted.inputs, 'outputs': arch_formatted.outputs }
            archs.append(arch)
        return archs
        
    def critiqueArchitecture(self, bitString):
        return self.client.getCritique(bitString)
        
        
    def ping(self):
        self.client.ping()
        print('ping()')
        
    def getOrbitList(self, problem):
        return self.client.getOrbitList(problem)
    
    def getInstrumentList(self, problem):
        return self.client.getInstrumentList(problem)
    

if __name__ == '__main__':
    try:
        #main()
        pass
    except Thrift.TException as tx:
        print('%s' % tx.message)
