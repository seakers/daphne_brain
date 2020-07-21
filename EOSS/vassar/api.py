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



class ObjectiveSatisfaction:
    def __init__(self, objective_name, satisfaction, weight):
        self.objective_name = objective_name
        self.satisfaction = satisfaction
        self.weight = weight



class VASSARClient:
    
    def __init__(self, port=9090, queue_name='test_queue', region_name='us-east-2'):

        # Boto3
        self.queue_name = queue_name
        self.region_name = region_name
        self.sqs = boto3.resource('sqs', endpoint_url='http://localstack:4576', region_name=self.region_name, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
        self.sqs_client = boto3.client('sqs', endpoint_url='http://localstack:4576', region_name=self.region_name, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
        self.problem_id = str(5)

        # Graphql Client
        self.dbClient = GraphqlClient()

    
    
    # deprecated
    def start_connection(self):
        return 0
    
    # deprecated
    def end_connection(self):
        return 0

    # deprecated
    def initialize_vassar_containers(self, group_id=1, problem_id=5):
        queues = self.sqs_client.list_queues()

        # GET CORRECT PRIVATE QUEUES
        queue_urls = []
        for url in queues['QueueUrls']:
            print(url)
            queue_info = self.sqs_client.list_queue_tags(QueueUrl=url)
            if 'Tags' in queue_info:
                queue_tags = queue_info['Tags']
                if 'problem_id' in queue_tags and 'type' in queue_tags:
                    if queue_tags['problem_id'] == str(self.problem_id) and queue_tags['type'] == 'vassar_eval_private':
                        queue_urls.append(url)
        
        print("---> QUEUE URLS TO INITIALIZE", queue_urls)
        for url in queue_urls:
            self.send_initialize_message(url, group_id, self.problem_id)

        return 0

    # working
    def send_initialize_message(self, url, group_id, problem_id):
        # Send init message
        privateQueue = self.sqs_client.send_message(QueueUrl=url, MessageBody='boto3', MessageAttributes={
            'msgType': {
                'StringValue': 'build',
                'DataType': 'String'
            },
            'group_id': {
                'StringValue': str(group_id),
                'DataType': 'String'
            },
            'problem_id': {
                'StringValue': str(self.problem_id),
                'DataType': 'String'
            }
        })

    # working
    def get_orbit_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_orbit_list(group_id, self.problem_id)
        orbits = [orbit['Orbit']['name'] for orbit in query['data']['Join__Problem_Orbit']]
        # hardcode = ['LEO-600-polar-NA', 'SSO-600-SSO-DD', 'SSO-600-SSO-AM', 'SSO-800-SSO-DD', 'SSO-800-SSO-AM']
        return orbits

    # working
    def get_instrument_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_instrument_list(group_id, self.problem_id)
        instruments = [instrument['Instrument']['name'] for instrument in query['data']['Join__Problem_Instrument']]
        # hardcode = ['SMAP_RAD', 'SMAP_MWR', 'VIIRS', 'CMIS', 'BIOMASS']
        # return hardcode
        return instruments

    # working
    def get_objective_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_objective_list(group_id, self.problem_id)
        print([obj['name'] for obj in query['data']['Stakeholder_Needs_Objective']])
        return [obj['name'] for obj in query['data']['Stakeholder_Needs_Objective']]

    # working
    def get_subobjective_list(self, problem, group_id=1, problem_id=5):
        query = self.dbClient.get_subobjective_list(group_id, self.problem_id)
        print([subobj['name'] for subobj in query['data']['Stakeholder_Needs_Subobjective']])
        return [subobj['name'] for subobj in query['data']['Stakeholder_Needs_Subobjective']]

    # working
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

        result = self.dbClient.subscribe_to_architecture(inputs, self.problem_id)
        
        if result == False:
            raise ValueError('---> Evaluation Timeout!!!!')

        result_formatted = result['data']['Architecture'][0]
        outputs = []
        outputs.append(result_formatted['science'])
        outputs.append(result_formatted['cost'])
        arch = {'id': result_formatted['id'], 'inputs': [b == "1" for b in result_formatted['input']], 'outputs': outputs}
        print('--> Arch: ' + str(arch))
        return arch

    # working
    def evaluate_false_architectures(self, problem_id, eval_queue_name='vassar_queue'):
        query_info = self.dbClient.get_false_architectures(self.problem_id)
        all_archs = query_info['data']['Architecture']
        evalQueue = self.sqs.get_queue_by_name(QueueName=eval_queue_name)
        for arch in all_archs:
            print("--> re-evaluate:", arch['input'])
            evalQueue.send_message(MessageBody='boto3', MessageAttributes={
                'msgType': {
                    'StringValue': 'evaluate',
                    'DataType': 'String'
                },
                'input': {
                    'StringValue': str(arch['input']),
                    'DataType': 'String'
                },
                'redo': {
                    'StringValue': 'true',
                    'DataType': 'String'
                }
            })

        return 0

    # working: test  
    def run_local_search(self, problem, inputs, problem_id=5, eval_queue_name='vassar_queue'):
        designs = []

        for x in range(4):
            new_design = self.random_local_change(inputs)
            print('---> NEW DESIGN: ', str(new_design))
            new_design_result = self.evaluate_architecture('SMAP', new_design, self.problem_id, eval_queue_name)
            print('---> RESULT: ', str(new_design_result))
            designs.append(new_design_result)

        return designs

    # working
    def random_local_change(self, inputs):
        index = random.randint(0, len(inputs)-1)
        new_bit = '1'
        if(inputs[index] == '0'):
            new_bit = '1'
        new_design = inputs[:index] + new_bit + inputs[index + 1:]
        return new_design

    # working
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

    # working
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
                'StringValue': str(self.problem_id),
                'DataType': 'String'
            },
            'ga_id': {
                'StringValue': ga_id,
                'DataType': 'String'
            }
        })

        return ga_id
    
    # deprecated 
    def create_thrift_arch(self, problem, arch):
        if problem in assignation_problems:
            return BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
        elif problem in partition_problems:
            return DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs))
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    # working
    def get_instruments_for_objective(self, problem, objective):
        # return self.client.getInstrumentsForObjective(problem, objective)
        print("--> Getting instrument for objective:", objective)
        query = self.dbClient.get_instrument_from_objective(objective)
        insts = [inst['name'] for inst in query['data']['Instrument']]
        return insts

    # working
    def get_instruments_for_panel(self, problem, panel):
        # return self.client.getInstrumentsForPanel(problem, panel)
        print("--> Getting instrument for panel:", panel)
        query = self.dbClient.get_instrument_from_panel(panel)
        insts = [inst['name'] for inst in query['data']['Instrument']]
        return insts
    
    # working
    def get_architecture_score_explanation(self, problem, arch):
        # thrift_arch = self.create_thrift_arch(problem, arch)
        # return self.client.getArchitectureScoreExplanation(problem, thrift_arch)
        print("--> Getting architecture score explanation for arch id:", arch)
        arch_id = self.dbClient.get_arch_id(arch)
        query = self.dbClient.get_architecture_score_explanation(arch_id)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Panel']['index_id'], expla['satisfaction'], expla['Stakeholder_Needs_Panel']['weight']) for expla in query['data']['ArchitectureScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working
    def get_panel_score_explanation(self, problem, arch, panel):
        # thrift_arch = self.create_thrift_arch(problem, arch)
        # return self.client.getPanelScoreExplanation(problem, thrift_arch, panel)
        print("--> get_panel_score_explanation:", arch.id, arch.inputs, arch.outputs, panel)
        arch_id = self.dbClient.get_arch_id(arch)
        query = self.dbClient.get_panel_score_explanation(arch_id, panel)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Objective']['name'], expla['satisfaction'], expla['Stakeholder_Needs_Objective']['weight']) for expla in query['data']['PanelScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working 
    def get_objective_score_explanation(self, problem, arch, objective):
        # thrift_arch = self.create_thrift_arch(problem, arch)
        # return self.client.getObjectiveScoreExplanation(problem, thrift_arch, objective)
        print("--> Getting objective score explanation for arch id:", arch)
        arch_id = self.dbClient.get_arch_id(arch)
        query = self.dbClient.get_objective_score_explanation(arch_id, objective)
        explanations = [ ObjectiveSatisfaction(expla['Stakeholder_Needs_Subobjective']['name'],  expla['satisfaction'], expla['Stakeholder_Needs_Subobjective']['weight']) for expla in query['data']['ObjectiveScoreExplanation'] ]
        print("--> explanations", explanations)
        return explanations

    # working
    def get_arch_science_information(self, problem, arch):
        print("\n\n----> get_arch_science_information", problem, arch)
        arch_id = self.dbClient.get_arch_id(arch)
        return self.dbClient.get_arch_science_information(arch_id)

    # working
    def get_arch_cost_information(self, problem, arch):
        print("\n\n----> get_arch_cost_information", problem, arch)
        arch_id = self.dbClient.get_arch_id(arch)
        return self.dbClient.get_arch_cost_information(arch_id)

    
    
    # rewrite
    def get_subscore_details(self, problem, arch, subobjective):
        print("\n\n----> get_subscore_details", problem, arch, subobjective)
        thrift_arch = self.create_thrift_arch(problem, arch)
        if problem in assignation_problems:
            return self.client.getSubscoreDetailsBinaryInput(problem, thrift_arch, subobjective)
        elif problem in partition_problems:
            return self.client.getSubscoreDetailsDiscreteInput(problem, thrift_arch, subobjective)
        else:
            raise ValueError('Problem {0} not recognized'.format(problem))

    # rewrite
    def critique_architecture(self, problem, arch):
        print("\n\n----> critique_architecture", problem, arch)
        arch_id = self.dbClient.get_arch_id(arch)
        return self.dbClient.get_arch_critique(arch_id)
    
    # rewrite
    def is_ga_running(self, ga_id):
        print("\n\n----> is_ga_running", ga_id)
        return self.client.isGARunning(ga_id)

    # rewrite
    def ping(self):
        self.client.ping()
        print('ping()')
        

