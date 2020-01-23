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
# Source: https://thrift-tutorial.readthedocs.io/en/latest/usage-example.html#a-more-complicated-example
#
import json

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from EDL.interface import DataMiningInterface

class EDLDataMiningClient:

    def __init__(self, port = 9191):
        # Make socket
        self.transport = TSocket.TSocket('localhost', port)

        # Buffering is critical. Rawsockets are very slow
        self.transport = TTransport.TBufferedTransport(self.transport)

        # Wrap in a protocol
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)

        # Create Client to use the protocol encoder
        self.client = DataMiningInterface.Client(self.protocol)

    def start_connection(self):
        # Connect
        self.transport.open()
    def end_connection(self):
        # Close!
        self.transport.close()

    def get_driving_features(self, file_path, class_no, no_params):
        return self.client.getDrivingFeaturesEpsilonMOEABinaryEDL("", "", file_path, class_no, no_params)
