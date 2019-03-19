#!/usr/bin/env python
import json
import sys,os
import glob

sys.path.append(os.path.dirname(__file__))

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from data_mining_API.interface import DataMiningInterface
from data_mining_API.interface.ttypes import BinaryInputArchitecture, DiscreteInputArchitecture, ContinuousInputArchitecture, Feature, AssigningProblemEntities, FlattenedConceptHierarchy

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
        
        _all_archs = []
        if inputType == "binary":
            for arch in all_archs:
                _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = self.client.getDrivingFeaturesBinary(problem, behavioral, non_behavioral, _all_archs, supp, conf, lift)

        elif inputType == "discrete":
            for arch in all_archs:
                _all_archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = self.client.getDrivingFeaturesDiscrete(problem, behavioral, non_behavioral, _all_archs, supp, conf, lift)

        else:
            raise NotImplementedError("Unsupported input type: {0}".format(inputType))

        drivingFeatures = []
        for df in _features:
            drivingFeatures.append({'id': df.id, 'name': df.name, 'expression': df.expression, 'metrics': df.metrics, 'complexity': df.complexity})

        return drivingFeatures

    def getDrivingFeaturesEpsilonMOEA(self, problem, inputType, behavioral, non_behavioral, all_archs):
        # try:
        print('getDrivingFeaturesEpsilonMOEA')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
        
        _all_archs = []
        if inputType == "binary":
            for arch in all_archs:
                _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = self.client.getDrivingFeaturesEpsilonMOEABinary(problem, behavioral, non_behavioral, _all_archs)

        elif inputType == "discrete":
            for arch in all_archs:
                _all_archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = self.client.getDrivingFeaturesEpsilonMOEADiscrete(problem, behavioral, non_behavioral, _all_archs)

        elif inputType == "continuous":
            for arch in all_archs:
                inputs = []
                for i in arch['inputs']:
                    if i is None:
                        pass
                    else:
                        inputs.append(float(i))
                        
                _all_archs.append(ContinuousInputArchitecture(arch['id'], inputs, arch['outputs']))
            _features = self.client.getDrivingFeaturesEpsilonMOEAContinuous(problem, behavioral, non_behavioral, _all_archs)

        drivingFeatures = []
        for df in _features:
            drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})

        return drivingFeatures

    def getDrivingFeaturesWithGeneralization(self, problem, inputType, behavioral, non_behavioral, all_archs):
        # try:
        print('getDrivingFeatures')
        print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
        
        _all_archs = []
        if inputType == "binary":
            for arch in all_archs:
                _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
            _features = self.client.getDrivingFeaturesWithGeneralizationBinary(problem, behavioral, non_behavioral, _all_archs)

        elif inputType == "discrete":
            raise NotImplementedError("Data mining with generalization not implemented for discrete input problem.")

        drivingFeatures = []
        for df in _features:
            drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics})

        return drivingFeatures
    
    def getMarginalDrivingFeatures(self, problem, inputType, behavioral, non_behavioral, all_archs, featureExpression,logicalConnective, supp, conf, lift):
        try:
            print('getMarginalDrivingFeatures')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            _all_archs = []
            if inputType == "binary":
                for arch in all_archs:
                    _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.client.getMarginalDrivingFeaturesBinary(problem, behavioral, non_behavioral, _all_archs, 

                                                                           featureExpression, logicalConnective, supp, conf, lift)

            elif inputType == "discrete":
                for arch in all_archs:
                    _all_archs.append(DiscreteInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))
                _features = self.client.getMarginalDrivingFeaturesDiscrete(problem, behavioral, non_behavioral, _all_archs, 
                                                                           featureExpression, logicalConnective, supp, conf, lift)
                        
            drivingFeatures = []
            
            for df in _features:
                drivingFeatures.append({'id':df.id,'name':df.name,'expression':df.expression,'metrics':df.metrics, 'complexity':df.complexity})
                
        except Exception as e:
            print('Exc in calling getMarginalDrivingFeatures(): '+str(e))

        return drivingFeatures

    def generalizeFeature(self, problem, inputType, behavioral, non_behavioral, all_archs, rootFeatureExpression, nodeFeatureExpression):
        try:
            print('running generalizeFeature()')
            print('b_length:{0}, nb_length:{1}, narchs:{2}'.format(len(behavioral),len(non_behavioral),len(all_archs)))
            
            _all_archs = []
            if inputType == "binary":
                for arch in all_archs:
                    _all_archs.append(BinaryInputArchitecture(arch.id, json.loads(arch.inputs), json.loads(arch.outputs)))

                _featuresWithDescription = self.client.generalizeFeatureBinary(problem, behavioral, non_behavioral, _all_archs, 
                                                                           rootFeatureExpression, nodeFeatureExpression)

            elif inputType == "discrete":
                raise NotImplementedError()
                        
            featuresWithDescription = []
            
            for feature in _featuresWithDescription:
                featuresWithDescription.append({'id':feature.id,
                    'name':feature.name,
                    'expression':feature.expression,
                    'metrics':feature.metrics, 
                    'complexity':feature.complexity,
                    'description':feature.description})
                
        except Exception as e:
            print('Exc in calling getMarginalDrivingFeatures(): '+str(e))

        return featuresWithDescription


    def setProblemParameters(self, problem, params):
        try:
            if problem == "ClimateCentric":
                entities = AssigningProblemEntities(params['instrument_list'], params['orbit_list'])
                self.client.setAssigningProblemEntities(problem, entities)

            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling setProblemParameters(): ' + str(e))


    def getProblemParameters(self, problem):
        params = None
        try:
            if problem == "ClimateCentric":
                params_ = self.client.getAssigningProblemEntities(problem)
                params = {}
                params['instrument_list'] = params_.leftSet
                params['orbit_list'] = params_.rightSet
                
            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling getProblemParameters(): '+str(e))

        return params

    def setProblemGeneralizedConcepts(self, problem, params):

        try:
            if problem == "ClimateCentric":

                orbit_generalized_concepts = []
                instrument_generalized_concepts = []

                for concept in params['orbit_extended_list']:
                    if concept in params['orbit_list']:
                        pass
                    else:
                        orbit_generalized_concepts.append(concept)

                for concept in params['instrument_extended_list']:
                    if concept in params['instrument_list']:
                        pass
                    else:
                        instrument_generalized_concepts.append(concept)

                entities = AssigningProblemEntities(instrument_generalized_concepts, orbit_generalized_concepts)
                self.client.setAssigningProblemGeneralizedConcepts(problem, entities)

            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling setProblemGeneralizedConcepts(): ' + str(e))

    def getProblemConceptHierarchy(self, problem, params):
        conceptHierarchy = None
        try:
            if problem == "ClimateCentric":
                params = AssigningProblemEntities(params["instrument_list"],params["orbit_list"])
                conceptHierarhcy_ = self.client.getAssigningProblemConceptHierarchy(problem, params)
                conceptHierarchy = {}
                conceptHierarchy['instanceMap'] = conceptHierarhcy_.instanceMap
                conceptHierarchy['superclassMap'] = conceptHierarhcy_.superclassMap
            else:
                raise NotImplementedError("Unsupported problem formulation: {0}".format(problem))

        except Exception as e:
            print('Exc in calling getTaxonomicScheme(): ' + str(e))

        return conceptHierarchy

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
            _arch = BinaryInputArchitecture(0, inputs, [])
            typicality = self.client.computeAlgebraicTypicality(_arch, expression)

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

