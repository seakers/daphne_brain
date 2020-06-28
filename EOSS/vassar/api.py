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
import os
import boto3
import random

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from EOSS.data.problem_specific import assignation_problems, partition_problems
from EOSS.vassar.interface import VASSARInterface
from EOSS.vassar.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture

from EOSS.graphql.api import GraphqlClient


ACCESS_KEY = 'AKIAJVM34C5MCCWRJCCQ'
SECRET_KEY = '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'


class VASSARClient:
    
    def __init__(self, port=9090, queue_name='test_queue', region_name='us-east-2'):

        # Boto3
        self.queue_name = queue_name
        self.region_name = region_name
        self.sqs = boto3.resource('sqs', endpoint_url='http://localstack:4576', region_name=self.region_name, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

        # Graphql Client
        self.dbClient = GraphqlClient()


    
    # This will now connect to SQS with Boto3 FINISHED
    def start_connection(self):
        return 0
    
    # End SQS connection with Boto3 FINISHED
    def end_connection(self):
        return 0


    # Boto3 query problem FINISHED
    def get_orbit_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_orbit_list(group_id, problem_id)
        print([orbit['name'] for orbit in query['data']['Orbit']])
        hardcode = ['LEO-600-polar-NA', 'SSO-600-SSO-DD', 'SSO-600-SSO-AM', 'SSO-800-SSO-DD', 'SSO-800-SSO-AM']
        return hardcode

    # Boto3 query problem FINISHED
    def get_instrument_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_instrument_list(group_id, problem_id)
        print([instrument['name'] for instrument in query['data']['Instrument']])
        hardcode = ['SMAP_RAD', 'SMAP_MWR', 'VIIRS', 'CMIS', 'BIOMASS']
        return hardcode

    # Boto3 query problem FINISHED
    def get_objective_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_objective_list(group_id, problem_id)
        print([obj['name'] for obj in query['data']['Stakeholder_Needs_Objective']])
        return [obj['name'] for obj in query['data']['Stakeholder_Needs_Objective']]

    # Boto3 query problem FINISHED
    def get_subobjective_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_subobjective_list(group_id, problem_id)
        print([subobj['name'] for subobj in query['data']['Stakeholder_Needs_Subobjective']])
        return [subobj['name'] for subobj in query['data']['Stakeholder_Needs_Subobjective']]

    
    # Move to frontend later -- dialogue functions
    def get_instruments_for_objective(self, problem, objective):
        return self.client.getInstrumentsForObjective(problem, objective)

    def get_instruments_for_panel(self, problem, panel):
        return self.client.getInstrumentsForPanel(problem, panel)


    # FINISHED
    def evaluate_architecture(self, problem, input_str, problem_id=5, eval_queue_name='vassar_queue'):
        inputs = ''
        for x in input_str:
            if x:
                inputs = inputs + '1'
            else:
                inputs = inputs + '0'
        
        # Connect to queue
        print("----------> Evaluating architecture ", inputs)

        evalQueue = self.sqs.get_queue_by_name(QueueName=eval_queue_name)

        evalQueue.send_message(MessageBody='boto3', MessageAttributes={
            'msgType': {
                'StringValue': 'evaluate',
                'DataType': 'String'
            },
            'input': {
                'StringValue': str(inputs),
                'DataType': 'String'
            }
        })

        result = self.dbClient.subscribe_to_architecture(inputs, problem_id)
        
        if result == False:
            raise ValueError('---> Evaluation Timeout!!!!')

        result_formatted = result['data']['Architecture'][0]
        outputs = []
        outputs.append(result_formatted['science'])
        outputs.append(result_formatted['cost'])
        arch = {'id': result_formatted['id'], 'inputs': result_formatted['input'], 'outputs': outputs}
        print('--> Arch: ' + str(arch))
        return arch


    
    
    # FINISHED  
    def run_local_search(self, problem, inputs, problem_id=5, eval_queue_name='vassar_queue'):
        designs = []

        for x in range(4):
            new_design = self.random_local_change(inputs)
            print('---> NEW DESIGN: ', str(new_design))
            new_design_result = self.evaluate_architecture('SMAP', new_design, problem_id, eval_queue_name)
            print('---> RESULT: ', str(new_design_result))
            designs.append(new_design_result)

        return designs

    def random_local_change(self, inputs):
        index = random.randint(0, len(inputs)-1)
        new_bit = '1'
        if(inputs[index] == '0'):
            new_bit = '1'
        new_design = inputs[:index] + new_bit + inputs[index + 1:]
        return new_design


    # TO BE IMPLEMENTED AFTER DEMO not
    def is_ga_running(self, ga_id):
        return self.client.isGARunning(ga_id)


    # TO BE IMPLEMENTED AFTER DEMO not
    def stop_ga(self, ga_id, ga_queue_name='algorithm_queue'):

        # Connect to queue
        gaQueue = self.sqs.get_queue_by_name(QueueName=ga_queue_name)

        gaQueue.send_message(MessageBody='boto3', MessageAttributes={
            'msgType': {
                'StringValue': 'stop_ga',
                'DataType': 'String'
            },
            'ga_id': {
                'StringValue': str(ga_id),
                'DataType': 'String'
            }
        })


        return 1 # return 0 if failure

    # TO BE IMPLEMENTED AFTER DEMO not
    # def start_ga(self, problem, username, thrift_list):
    def start_ga(self, ga_queue_name='algorithm_queue'):

        # Connect to queue
        gaQueue = self.sqs.get_queue_by_name(QueueName=ga_queue_name)

        # Create ga_id
        # ga_id = 'test_ga_' + str(random.random())
        ga_id = 'test_ga_1'

        gaQueue.send_message(MessageBody='boto3', MessageAttributes={
            'msgType': {
                'StringValue': 'start_ga',
                'DataType': 'String'
            },
            'maxEvals': {
                'StringValue': '3000',
                'DataType': 'String'
            },
            'crossoverProbability': {
                'StringValue': '1',
                'DataType': 'String'
            },
            'mutationProbability': {
                'StringValue': '0.016666',
                'DataType': 'String'
            },
            'group_id': {
                'StringValue': '1',
                'DataType': 'String'
            },
            'problem_id': {
                'StringValue': '5',
                'DataType': 'String'
            },
            'ga_id': {
                'StringValue': ga_id,
                'DataType': 'String'
            }
        })

        return ga_id

    
    
    
    
    
    
    # TO BE IMPLEMENTED AFTER DEMO
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





    def ping(self):
        self.client.ping()
        print('ping()')
        

