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
from data_mining_interface import DataMiningInterface
from data_mining_interface.ttypes import Architecture, DrivingFeature

class data_mining_client():
    
    def __init__(self):
        # Make socket
        self.transport = TSocket.TSocket('localhost', 9191)
    
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
        
    def getDrivingFeatures(self, behavioral, non_behavioral, all_archs, supp, conf, lift):
        #self.client.ping()
        print('getDrivingFeatures')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
        print(type(behavioral[0]))
        print(type(non_behavioral[0]))
        print(all_archs[0])
        print(supp)
        print(conf)
        print(lift)
        
        archs_formatted = []
        for arch in all_archs:
            archs_formatted.append(Architecture(arch['id'],arch['bitString'],arch['science'],arch['cost']))
        
        drivingFeatures_formatted = self.client.getDrivingFeatures(behavioral, non_behavioral, archs_formatted, supp, conf, lift)
        
        drivingFeatures = []
        for df in drivingFeatures_formatted:
            drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})
        
        return drivingFeatures


    

if __name__ == '__main__':
    try:
        #main()
        pass
    except Thrift.TException as tx:
        print('%s' % tx.message)
