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

import sys,os
import glob

sys.path.append(os.path.dirname(__file__))

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from data_mining_API.interface import interface as DataMiningInterface
from data_mining_API.interface.ttypes import BinaryInputArchitecture, Feature


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
        
    def getDrivingFeatures(self, behavioral, non_behavioral, all_archs, supp, conf, lift):
        try:
            print('getDrivingFeatures')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            archs_formatted = []
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch['id'],arch['inputs'],arch['outputs']))
    
            drivingFeatures_formatted = self.client.getDrivingFeatures(behavioral, non_behavioral, archs_formatted, supp, conf, lift)
            drivingFeatures = []
            
            for df in drivingFeatures_formatted:
                drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})
        except Exception:
            print(Exception)

        return drivingFeatures

    
    def getMarginalDrivingFeaturesConjunctive(self, behavioral, non_behavioral, all_archs, featureName, archs_with_feature, supp, conf, lift):
        try:
            print('getMarginalDrivingFeatures')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            archs_formatted = []
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch['id'],arch['inputs'],arch['outputs']))
                    
            drivingFeatures_formatted = self.client.getMarginalDrivingFeatures(behavioral, non_behavioral, archs_formatted, 
                                                                       featureName, archs_with_feature, supp, conf, lift)
                        
            drivingFeatures = []
            
            for df in drivingFeatures_formatted:
                drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})
                
        except Exception:
            print(Exception)

        return drivingFeatures

    
        
    def getMarginalDrivingFeatures(self, behavioral, non_behavioral, all_archs, featureExpression, supp, conf, lift):
        try:
            print('getMarginalDrivingFeatures')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            archs_formatted = []
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch['id'],arch['inputs'],arch['outputs']))
                    
            drivingFeatures_formatted = self.client.getMarginalDrivingFeatures(behavioral, non_behavioral, archs_formatted, 
                                                                       featureExpression, supp, conf, lift)
                        
            drivingFeatures = []
            
            for df in drivingFeatures_formatted:
                drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})
                
        except Exception:
            print(Exception)

        return drivingFeatures
