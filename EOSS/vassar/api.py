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
import json

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.interface import VASSARInterface
from EOSS.vassar.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture


class VASSARClient:
    
    def __init__(self, port=9090):
        # Make socket
        self.transport = TSocket.TSocket('localhost', port)
    
        # Buffering is critical. Raw sockets are very slow
        self.transport = TTransport.TBufferedTransport(self.transport)
    
        # Wrap in a protocol
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)

        # Create a client to use the protocol encoder
        self.client = VASSARInterface.Client(self.protocol)

    def start_connection(self):
        # Connect
        self.transport.open()
    
    def end_connection(self):
        # Close
        self.transport.close()

    def get_orbit_list(self, problem):
        return self.client.getOrbitList(problem)

    def get_instrument_list(self, problem):
        return self.client.getInstrumentList(problem)

    def get_objective_list(self, problem):
        return self.client.getObjectiveList(problem)

    def get_subobjective_list(self, problem):
        return self.client.getSubobjectiveList(problem)

    def get_instruments_for_objective(self, problem, objective):
        return self.client.getInstrumentsForObjective(problem, objective)

    def get_instruments_for_panel(self, problem, panel):
        return self.client.getInstrumentsForPanel(problem, panel)
    
    def evaluate_architecture(self, problem, inputs):
        if problem in assignation_problems:
            arch_formatted = self.client.evalBinaryInputArch(problem, inputs)
        elif problem in partition_problems:
            arch_formatted = self.client.evalDiscreteInputArch(problem, inputs)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))
        arch = {'id': arch_formatted.id, 'inputs': arch_formatted.inputs, 'outputs': arch_formatted.outputs}
        return arch

    def run_local_search(self, problem, arch):
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            archs_formatted = self.client.runLocalSearchBinaryInput(problem, thrift_arch)
        elif problem in partition_problems:
            archs_formatted = self.client.runLocalSearchDiscreteInput(problem, thrift_arch)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))
        archs = []
        for arch_formatted in archs_formatted:
            arch = {'id': arch_formatted.id, 'inputs': arch_formatted.inputs, 'outputs': arch_formatted.outputs}
            archs.append(arch)
        return archs

    def create_thrift_arch(self, problem, arch):
        if problem in assignation_problems:
            return BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
        elif problem in partition_problems:
            return DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    def get_architecture_score_explanation(self, problem, arch):
        thrift_arch = self.create_thrift_arch(problem, arch)
        return self.client.getArchitectureScoreExplanation(problem, thrift_arch)

    def get_panel_score_explanation(self, problem, arch, panel):
        thrift_arch = self.create_thrift_arch(problem, arch)
        return self.client.getPanelScoreExplanation(problem, thrift_arch, panel)

    def get_objective_score_explanation(self, problem, arch, objective):
        thrift_arch = self.create_thrift_arch(problem, arch)
        return self.client.getObjectiveScoreExplanation(problem, thrift_arch, objective)

    def get_arch_science_information(self, problem, arch):
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            return self.client.getArchScienceInformationBinaryInput(problem, thrift_arch)
        elif problem in partition_problems:
            return self.client.getArchScienceInformationDiscreteInput(problem, thrift_arch)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    def get_arch_cost_information(self, problem, arch):
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            return self.client.getArchCostInformationBinaryInput(problem, thrift_arch)
        elif problem in partition_problems:
            return self.client.getArchCostInformationDiscreteInput(problem, thrift_arch)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    def get_subscore_details(self, problem, arch, subobjective):
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            return self.client.getSubscoreDetailsBinaryInput(problem, thrift_arch, subobjective)
        elif problem in partition_problems:
            return self.client.getSubscoreDetailsDiscreteInput(problem, thrift_arch, subobjective)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    def critique_architecture(self, problem, arch):
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            return self.client.getCritiqueBinaryInputArch(problem, thrift_arch)
        elif problem in partition_problems:
            return self.client.getCritiqueDiscreteInputArch(problem, thrift_arch)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    def stop_ga(self, ga_id):
        return self.client.stopGA(ga_id)

    def is_ga_running(self, ga_id):
        return self.client.isGARunning(ga_id)

    def start_ga(self, problem, username, thrift_list):
        if problem in assignation_problems:
            ga_id = self.client.startGABinaryInput(problem, thrift_list, username)
        elif problem in partition_problems:
            ga_id = self.client.startGADiscreteInput(problem, thrift_list, username)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))
        return ga_id

    def ping(self):
        self.client.ping()
        print('ping()')
        

