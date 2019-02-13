#!/usr/bin/env python
import json
import sys,os
import glob

sys.path.append(os.path.dirname(__file__))

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from data_mining_API.interface import interface as DataMiningInterface
from data_mining_API.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture, Feature, AssigningProblemParameters


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
        
    def getDrivingFeatures(self, problem, inputType, behavioral, non_behavioral, all_archs, supp, conf, lift):
        # try:
        print('getDrivingFeatures')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral), len(non_behavioral), len(all_archs)))
        
        archs_formatted = []
        if inputType == "binary":
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.getDrivingFeaturesBinary(problem, behavioral, non_behavioral, archs_formatted, supp, conf, lift)

        elif inputType == "discrete":
            for arch in all_archs:
                archs_formatted.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.getDrivingFeaturesDiscrete(problem, behavioral, non_behavioral, archs_formatted, supp, conf, lift)

        drivingFeatures = []
        for df in drivingFeatures_formatted:
            drivingFeatures.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics, 'complexity': df.complexity})

        # except Exception as e:
        #     print("Exc in getDrivingFeatures: " + str(e))

        return drivingFeatures

    def getDrivingFeaturesEpsilonMOEA(self, problem, inputType, behavioral, non_behavioral, all_archs):
        # try:
        print('getDrivingFeaturesEpsilonMOEA')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
        
        archs_formatted = []
        if inputType == "binary":
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.getDrivingFeaturesEpsilonMOEABinary(problem, behavioral, non_behavioral, archs_formatted)

        elif inputType == "discrete":
            for arch in all_archs:
                archs_formatted.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.getDrivingFeaturesEpsilonMOEADiscrete(problem, behavioral, non_behavioral, archs_formatted)

        drivingFeatures = []
        for df in drivingFeatures_formatted:
            drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})

        return drivingFeatures

    def getDrivingFeaturesWithGeneralization(self, problem, inputType, behavioral, non_behavioral, all_archs):
        # try:
        print('getDrivingFeatures')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
        
        archs_formatted = []
        if inputType == "binary":
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.getDrivingFeaturesWithGeneralizationBinary(problem, behavioral, non_behavioral, archs_formatted)

        elif inputType == "discrete":
            raise ValueError("Data mining with generalization not implemented for discrete input problem.")

        drivingFeatures = []
        for df in drivingFeatures_formatted:
            drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})

        return drivingFeatures
    
    def getDrivingFeaturesAutomated(self, problem, inputType, behavioral, non_behavioral, all_archs, supp, conf, lift):
        # try:
        print('getDrivingFeatures')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
        
        archs_formatted = []
        if inputType == "binary":
            for arch in all_archs:
                archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.runAutomatedLocalSearchBinary(problem, behavioral, non_behavioral, archs_formatted, supp, conf, lift)

        elif inputType == "discrete":
            for arch in all_archs:
                archs_formatted.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            drivingFeatures_formatted = self.client.runAutomatedLocalSearchDiscrete(problem, behavioral, non_behavioral, archs_formatted, supp, conf, lift)

        drivingFeatures = []
        for df in drivingFeatures_formatted:
            drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics, 'complexity':df.complexity})

        # except Exception as e:
        #     print("Exc in getDrivingFeatures: " + str(e))

        return drivingFeatures
        
    def getMarginalDrivingFeatures(self, problem, inputType, behavioral, non_behavioral, all_archs, featureExpression,logicalConnective, supp, conf, lift):
        try:
            print('getMarginalDrivingFeatures')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            archs_formatted = []
            if inputType == "binary":
                for arch in all_archs:
                    archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                drivingFeatures_formatted = self.client.getMarginalDrivingFeaturesBinary(problem, behavioral, non_behavioral, archs_formatted, 
                                                                           featureExpression, logicalConnective, supp, conf, lift)

            elif inputType == "discrete":
                for arch in all_archs:
                    archs_formatted.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                drivingFeatures_formatted = self.client.getMarginalDrivingFeaturesDiscrete(problem, behavioral, non_behavioral, archs_formatted, 
                                                                           featureExpression, logicalConnective, supp, conf, lift)
                        
            drivingFeatures = []
            
            for df in drivingFeatures_formatted:
                drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics, 'complexity':df.complexity})
                
        except Exception as e:
            print('Exc in calling getMarginalDrivingFeatures(): '+str(e))

        return drivingFeatures

    def runGeneralizationLocalSearch(self, problem, inputType, behavioral, non_behavioral, all_archs, featureExpression):
        try:
            print('runGeneralizationLocalSearch')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            archs_formatted = []
            if inputType == "binary":
                for arch in all_archs:
                    archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                drivingFeatures_formatted = self.client.runInputGeneralizationLocalSearchBinary(problem, behavioral, non_behavioral, 
                                                                            archs_formatted, 
                                                                           featureExpression)
                
            elif inputType == "discrete":
                raise ValueError("Not implemented yet")

            drivingFeatures = []
            for df in drivingFeatures_formatted:
                drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics, 'complexity':df.complexity})
                
        except Exception as e:
            print('Exc in calling getMarginalDrivingFeatures(): '+str(e))

        return drivingFeatures


    def runAutomatedLocalSearch(self, problem, input_type, behavioral, non_behavioral, all_archs,
                                support_threshold, confidence_threshold, lift_threshold):
        try:
            print('runAutomatedLocalSearch')
            print(
                'b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral), len(non_behavioral), len(all_archs)))

            archs_formatted = []
            if input_type == "binary":
                for arch in all_archs:
                    archs_formatted.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                drivingFeatures_formatted = self.client.runAutomatedLocalSearchBinary(problem,
                                                                                      behavioral,
                                                                                      non_behavioral,
                                                                                      archs_formatted,
                                                                                      support_threshold,
                                                                                      confidence_threshold,
                                                                                      lift_threshold)

            elif input_type == "discrete":
                for arch in all_archs:
                    archs_formatted.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                drivingFeatures_formatted = self.client.runAutomatedLocalSearchDiscrete(problem,
                                                                                        behavioral,
                                                                                        non_behavioral,
                                                                                        archs_formatted,
                                                                                        support_threshold,
                                                                                        confidence_threshold,
                                                                                        lift_threshold)

            drivingFeatures = []
            for df in drivingFeatures_formatted:
                drivingFeatures.append(
                    {'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics,
                     'complexity': df.complexity})

        except Exception as e:
            print('Exc in calling getMarginalDrivingFeatures(): ' + str(e))

        return drivingFeatures

    def setProblemParameters(self, problem, params):
        try:
            if problem == "ClimateCentric":
                pass

            else:
                raise ValueError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling setProblemParameters(): '+str(e))

    def getProblemParameters(self, problem):
        params = None
        try:
            if problem == "ClimateCentric":
                params_ = self.client.getAssigningProblemParameters(problem)
                params = {}
                params['orbitList'] = params_.orbitList
                params['instrumentList'] = params_.instrumentList
            else:
                raise ValueError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling getProblemParameters(): '+str(e))

        return params

    def getTaxonomicScheme(self, problem, params):
        scheme = None
        try:
            if problem == "ClimateCentric":
                params = AssigningProblemParameters(params["orbitList"], params["instrumentList"])
                scheme_ = self.client.getAssigningProblemTaxonomicScheme(problem, params)
                scheme = {}
                scheme['instanceMap'] = scheme_.instanceMap
                scheme['superclassMap'] = scheme_.superclassMap
            else:
                raise ValueError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling getTaxonomicScheme(): ' + str(e))

        return scheme

    def convertToDNF(self, expression):
        try:
            dnf_expression = self.client.convertToDNF(expression)
        except Exception as e:
            print('Exc in calling convertToDNF(): '+str(e))

        return dnf_expression

    def convertToCNF(self, expression):
        try:
            cnf_expression = self.client.convertToCNF(expression)
        except Exception as e:
            print('Exc in calling convertToCNF(): '+str(e))

        return cnf_expression

    def computeTypicality(self, inputs, expression):
        try:
            arch_formatted = BinaryInputArchitecture(0, inputs, [])
            typicality = self.client.computeAlgebraicTypicality(arch_formatted, expression)

        except Exception as e:
            print('Exc in calling computeComplexity(): '+str(e))

        return typicality

    def computeComplexity(self, expression):
        try:
            complexity = self.client.computeComplexity(expression)
        except Exception as e:
            print('Exc in calling computeComplexity(): '+str(e))

        return complexity

    def computeComplexityOfFeatures(self, expressions):
        try:
            complexity_values = self.client.computeComplexityOfFeatures(expressions)
        except Exception as e:
            print('Exc in calling computeComplexityOfFeatures(): '+str(e))

        return complexity_values

