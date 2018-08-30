#
# Autogenerated by Thrift Compiler (0.11.0)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TFrozenDict, TException, TApplicationException
from thrift.protocol.TProtocol import TProtocolException
from thrift.TRecursive import fix_spec

import sys

from thrift.transport import TTransport
all_structs = []


class BinaryInputArchitecture(object):
    """
    Structs are the basic complex data structures. They are comprised of fields
    which each have an integer identifier, a type, a symbolic name, and an
    optional default value.

    Fields can be declared "optional", which ensures they will not be included
    in the serialized output if they aren't set.  Note that this requires some
    manual management in some languages.

    Attributes:
     - id
     - inputs
     - outputs
    """


    def __init__(self, id=None, inputs=None, outputs=None,):
        self.id = id
        self.inputs = inputs
        self.outputs = outputs

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    self.id = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.inputs = []
                    (_etype3, _size0) = iprot.readListBegin()
                    for _i4 in range(_size0):
                        _elem5 = iprot.readBool()
                        self.inputs.append(_elem5)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.outputs = []
                    (_etype9, _size6) = iprot.readListBegin()
                    for _i10 in range(_size6):
                        _elem11 = iprot.readDouble()
                        self.outputs.append(_elem11)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('BinaryInputArchitecture')
        if self.id is not None:
            oprot.writeFieldBegin('id', TType.I32, 1)
            oprot.writeI32(self.id)
            oprot.writeFieldEnd()
        if self.inputs is not None:
            oprot.writeFieldBegin('inputs', TType.LIST, 2)
            oprot.writeListBegin(TType.BOOL, len(self.inputs))
            for iter12 in self.inputs:
                oprot.writeBool(iter12)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.outputs is not None:
            oprot.writeFieldBegin('outputs', TType.LIST, 3)
            oprot.writeListBegin(TType.DOUBLE, len(self.outputs))
            for iter13 in self.outputs:
                oprot.writeDouble(iter13)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class DiscreteInputArchitecture(object):
    """
    Attributes:
     - id
     - inputs
     - outputs
    """


    def __init__(self, id=None, inputs=None, outputs=None,):
        self.id = id
        self.inputs = inputs
        self.outputs = outputs

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    self.id = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.inputs = []
                    (_etype17, _size14) = iprot.readListBegin()
                    for _i18 in range(_size14):
                        _elem19 = iprot.readI32()
                        self.inputs.append(_elem19)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.outputs = []
                    (_etype23, _size20) = iprot.readListBegin()
                    for _i24 in range(_size20):
                        _elem25 = iprot.readDouble()
                        self.outputs.append(_elem25)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('DiscreteInputArchitecture')
        if self.id is not None:
            oprot.writeFieldBegin('id', TType.I32, 1)
            oprot.writeI32(self.id)
            oprot.writeFieldEnd()
        if self.inputs is not None:
            oprot.writeFieldBegin('inputs', TType.LIST, 2)
            oprot.writeListBegin(TType.I32, len(self.inputs))
            for iter26 in self.inputs:
                oprot.writeI32(iter26)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.outputs is not None:
            oprot.writeFieldBegin('outputs', TType.LIST, 3)
            oprot.writeListBegin(TType.DOUBLE, len(self.outputs))
            for iter27 in self.outputs:
                oprot.writeDouble(iter27)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class ObjectiveSatisfaction(object):
    """
    Attributes:
     - objective_name
     - satisfaction
     - weight
    """


    def __init__(self, objective_name=None, satisfaction=None, weight=None,):
        self.objective_name = objective_name
        self.satisfaction = satisfaction
        self.weight = weight

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.objective_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.DOUBLE:
                    self.satisfaction = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.DOUBLE:
                    self.weight = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('ObjectiveSatisfaction')
        if self.objective_name is not None:
            oprot.writeFieldBegin('objective_name', TType.STRING, 1)
            oprot.writeString(self.objective_name.encode('utf-8') if sys.version_info[0] == 2 else self.objective_name)
            oprot.writeFieldEnd()
        if self.satisfaction is not None:
            oprot.writeFieldBegin('satisfaction', TType.DOUBLE, 2)
            oprot.writeDouble(self.satisfaction)
            oprot.writeFieldEnd()
        if self.weight is not None:
            oprot.writeFieldBegin('weight', TType.DOUBLE, 3)
            oprot.writeDouble(self.weight)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class SubscoreInformation(object):
    """
    Attributes:
     - name
     - description
     - value
     - weight
     - subscores
    """


    def __init__(self, name=None, description=None, value=None, weight=None, subscores=None,):
        self.name = name
        self.description = description
        self.value = value
        self.weight = weight
        self.subscores = subscores

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRING:
                    self.description = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.DOUBLE:
                    self.value = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.DOUBLE:
                    self.weight = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.LIST:
                    self.subscores = []
                    (_etype31, _size28) = iprot.readListBegin()
                    for _i32 in range(_size28):
                        _elem33 = SubscoreInformation()
                        _elem33.read(iprot)
                        self.subscores.append(_elem33)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('SubscoreInformation')
        if self.name is not None:
            oprot.writeFieldBegin('name', TType.STRING, 1)
            oprot.writeString(self.name.encode('utf-8') if sys.version_info[0] == 2 else self.name)
            oprot.writeFieldEnd()
        if self.description is not None:
            oprot.writeFieldBegin('description', TType.STRING, 2)
            oprot.writeString(self.description.encode('utf-8') if sys.version_info[0] == 2 else self.description)
            oprot.writeFieldEnd()
        if self.value is not None:
            oprot.writeFieldBegin('value', TType.DOUBLE, 3)
            oprot.writeDouble(self.value)
            oprot.writeFieldEnd()
        if self.weight is not None:
            oprot.writeFieldBegin('weight', TType.DOUBLE, 4)
            oprot.writeDouble(self.weight)
            oprot.writeFieldEnd()
        if self.subscores is not None:
            oprot.writeFieldBegin('subscores', TType.LIST, 5)
            oprot.writeListBegin(TType.STRUCT, len(self.subscores))
            for iter34 in self.subscores:
                iter34.write(oprot)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class MissionCostInformation(object):
    """
    Attributes:
     - orbit_name
     - payload
     - launch_vehicle
     - total_mass
     - total_power
     - total_cost
     - mass_budget
     - power_budget
     - cost_budget
    """


    def __init__(self, orbit_name=None, payload=None, launch_vehicle=None, total_mass=None, total_power=None, total_cost=None, mass_budget=None, power_budget=None, cost_budget=None,):
        self.orbit_name = orbit_name
        self.payload = payload
        self.launch_vehicle = launch_vehicle
        self.total_mass = total_mass
        self.total_power = total_power
        self.total_cost = total_cost
        self.mass_budget = mass_budget
        self.power_budget = power_budget
        self.cost_budget = cost_budget

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.orbit_name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.payload = []
                    (_etype38, _size35) = iprot.readListBegin()
                    for _i39 in range(_size35):
                        _elem40 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.payload.append(_elem40)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.STRING:
                    self.launch_vehicle = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.DOUBLE:
                    self.total_mass = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.DOUBLE:
                    self.total_power = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.DOUBLE:
                    self.total_cost = iprot.readDouble()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.MAP:
                    self.mass_budget = {}
                    (_ktype42, _vtype43, _size41) = iprot.readMapBegin()
                    for _i45 in range(_size41):
                        _key46 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val47 = iprot.readDouble()
                        self.mass_budget[_key46] = _val47
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.MAP:
                    self.power_budget = {}
                    (_ktype49, _vtype50, _size48) = iprot.readMapBegin()
                    for _i52 in range(_size48):
                        _key53 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val54 = iprot.readDouble()
                        self.power_budget[_key53] = _val54
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.MAP:
                    self.cost_budget = {}
                    (_ktype56, _vtype57, _size55) = iprot.readMapBegin()
                    for _i59 in range(_size55):
                        _key60 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val61 = iprot.readDouble()
                        self.cost_budget[_key60] = _val61
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('MissionCostInformation')
        if self.orbit_name is not None:
            oprot.writeFieldBegin('orbit_name', TType.STRING, 1)
            oprot.writeString(self.orbit_name.encode('utf-8') if sys.version_info[0] == 2 else self.orbit_name)
            oprot.writeFieldEnd()
        if self.payload is not None:
            oprot.writeFieldBegin('payload', TType.LIST, 2)
            oprot.writeListBegin(TType.STRING, len(self.payload))
            for iter62 in self.payload:
                oprot.writeString(iter62.encode('utf-8') if sys.version_info[0] == 2 else iter62)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.launch_vehicle is not None:
            oprot.writeFieldBegin('launch_vehicle', TType.STRING, 3)
            oprot.writeString(self.launch_vehicle.encode('utf-8') if sys.version_info[0] == 2 else self.launch_vehicle)
            oprot.writeFieldEnd()
        if self.total_mass is not None:
            oprot.writeFieldBegin('total_mass', TType.DOUBLE, 4)
            oprot.writeDouble(self.total_mass)
            oprot.writeFieldEnd()
        if self.total_power is not None:
            oprot.writeFieldBegin('total_power', TType.DOUBLE, 5)
            oprot.writeDouble(self.total_power)
            oprot.writeFieldEnd()
        if self.total_cost is not None:
            oprot.writeFieldBegin('total_cost', TType.DOUBLE, 6)
            oprot.writeDouble(self.total_cost)
            oprot.writeFieldEnd()
        if self.mass_budget is not None:
            oprot.writeFieldBegin('mass_budget', TType.MAP, 7)
            oprot.writeMapBegin(TType.STRING, TType.DOUBLE, len(self.mass_budget))
            for kiter63, viter64 in self.mass_budget.items():
                oprot.writeString(kiter63.encode('utf-8') if sys.version_info[0] == 2 else kiter63)
                oprot.writeDouble(viter64)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        if self.power_budget is not None:
            oprot.writeFieldBegin('power_budget', TType.MAP, 8)
            oprot.writeMapBegin(TType.STRING, TType.DOUBLE, len(self.power_budget))
            for kiter65, viter66 in self.power_budget.items():
                oprot.writeString(kiter65.encode('utf-8') if sys.version_info[0] == 2 else kiter65)
                oprot.writeDouble(viter66)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        if self.cost_budget is not None:
            oprot.writeFieldBegin('cost_budget', TType.MAP, 9)
            oprot.writeMapBegin(TType.STRING, TType.DOUBLE, len(self.cost_budget))
            for kiter67, viter68 in self.cost_budget.items():
                oprot.writeString(kiter67.encode('utf-8') if sys.version_info[0] == 2 else kiter67)
                oprot.writeDouble(viter68)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class SubobjectiveDetails(object):
    """
    Attributes:
     - param
     - attr_names
     - attr_values
     - scores
     - taken_by
     - justifications
    """


    def __init__(self, param=None, attr_names=None, attr_values=None, scores=None, taken_by=None, justifications=None,):
        self.param = param
        self.attr_names = attr_names
        self.attr_values = attr_values
        self.scores = scores
        self.taken_by = taken_by
        self.justifications = justifications

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, [self.__class__, self.thrift_spec])
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.param = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.LIST:
                    self.attr_names = []
                    (_etype72, _size69) = iprot.readListBegin()
                    for _i73 in range(_size69):
                        _elem74 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.attr_names.append(_elem74)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.LIST:
                    self.attr_values = []
                    (_etype78, _size75) = iprot.readListBegin()
                    for _i79 in range(_size75):
                        _elem80 = []
                        (_etype84, _size81) = iprot.readListBegin()
                        for _i85 in range(_size81):
                            _elem86 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                            _elem80.append(_elem86)
                        iprot.readListEnd()
                        self.attr_values.append(_elem80)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.LIST:
                    self.scores = []
                    (_etype90, _size87) = iprot.readListBegin()
                    for _i91 in range(_size87):
                        _elem92 = iprot.readDouble()
                        self.scores.append(_elem92)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.LIST:
                    self.taken_by = []
                    (_etype96, _size93) = iprot.readListBegin()
                    for _i97 in range(_size93):
                        _elem98 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.taken_by.append(_elem98)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.LIST:
                    self.justifications = []
                    (_etype102, _size99) = iprot.readListBegin()
                    for _i103 in range(_size99):
                        _elem104 = []
                        (_etype108, _size105) = iprot.readListBegin()
                        for _i109 in range(_size105):
                            _elem110 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                            _elem104.append(_elem110)
                        iprot.readListEnd()
                        self.justifications.append(_elem104)
                    iprot.readListEnd()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, [self.__class__, self.thrift_spec]))
            return
        oprot.writeStructBegin('SubobjectiveDetails')
        if self.param is not None:
            oprot.writeFieldBegin('param', TType.STRING, 1)
            oprot.writeString(self.param.encode('utf-8') if sys.version_info[0] == 2 else self.param)
            oprot.writeFieldEnd()
        if self.attr_names is not None:
            oprot.writeFieldBegin('attr_names', TType.LIST, 2)
            oprot.writeListBegin(TType.STRING, len(self.attr_names))
            for iter111 in self.attr_names:
                oprot.writeString(iter111.encode('utf-8') if sys.version_info[0] == 2 else iter111)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.attr_values is not None:
            oprot.writeFieldBegin('attr_values', TType.LIST, 3)
            oprot.writeListBegin(TType.LIST, len(self.attr_values))
            for iter112 in self.attr_values:
                oprot.writeListBegin(TType.STRING, len(iter112))
                for iter113 in iter112:
                    oprot.writeString(iter113.encode('utf-8') if sys.version_info[0] == 2 else iter113)
                oprot.writeListEnd()
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.scores is not None:
            oprot.writeFieldBegin('scores', TType.LIST, 4)
            oprot.writeListBegin(TType.DOUBLE, len(self.scores))
            for iter114 in self.scores:
                oprot.writeDouble(iter114)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.taken_by is not None:
            oprot.writeFieldBegin('taken_by', TType.LIST, 5)
            oprot.writeListBegin(TType.STRING, len(self.taken_by))
            for iter115 in self.taken_by:
                oprot.writeString(iter115.encode('utf-8') if sys.version_info[0] == 2 else iter115)
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        if self.justifications is not None:
            oprot.writeFieldBegin('justifications', TType.LIST, 6)
            oprot.writeListBegin(TType.LIST, len(self.justifications))
            for iter116 in self.justifications:
                oprot.writeListBegin(TType.STRING, len(iter116))
                for iter117 in iter116:
                    oprot.writeString(iter117.encode('utf-8') if sys.version_info[0] == 2 else iter117)
                oprot.writeListEnd()
            oprot.writeListEnd()
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
all_structs.append(BinaryInputArchitecture)
BinaryInputArchitecture.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'id', None, None, ),  # 1
    (2, TType.LIST, 'inputs', (TType.BOOL, None, False), None, ),  # 2
    (3, TType.LIST, 'outputs', (TType.DOUBLE, None, False), None, ),  # 3
)
all_structs.append(DiscreteInputArchitecture)
DiscreteInputArchitecture.thrift_spec = (
    None,  # 0
    (1, TType.I32, 'id', None, None, ),  # 1
    (2, TType.LIST, 'inputs', (TType.I32, None, False), None, ),  # 2
    (3, TType.LIST, 'outputs', (TType.DOUBLE, None, False), None, ),  # 3
)
all_structs.append(ObjectiveSatisfaction)
ObjectiveSatisfaction.thrift_spec = (
    None,  # 0
    (1, TType.STRING, 'objective_name', 'UTF8', None, ),  # 1
    (2, TType.DOUBLE, 'satisfaction', None, None, ),  # 2
    (3, TType.DOUBLE, 'weight', None, None, ),  # 3
)
all_structs.append(SubscoreInformation)
SubscoreInformation.thrift_spec = (
    None,  # 0
    (1, TType.STRING, 'name', 'UTF8', None, ),  # 1
    (2, TType.STRING, 'description', 'UTF8', None, ),  # 2
    (3, TType.DOUBLE, 'value', None, None, ),  # 3
    (4, TType.DOUBLE, 'weight', None, None, ),  # 4
    (5, TType.LIST, 'subscores', (TType.STRUCT, [SubscoreInformation, None], False), None, ),  # 5
)
all_structs.append(MissionCostInformation)
MissionCostInformation.thrift_spec = (
    None,  # 0
    (1, TType.STRING, 'orbit_name', 'UTF8', None, ),  # 1
    (2, TType.LIST, 'payload', (TType.STRING, 'UTF8', False), None, ),  # 2
    (3, TType.STRING, 'launch_vehicle', 'UTF8', None, ),  # 3
    (4, TType.DOUBLE, 'total_mass', None, None, ),  # 4
    (5, TType.DOUBLE, 'total_power', None, None, ),  # 5
    (6, TType.DOUBLE, 'total_cost', None, None, ),  # 6
    (7, TType.MAP, 'mass_budget', (TType.STRING, 'UTF8', TType.DOUBLE, None, False), None, ),  # 7
    (8, TType.MAP, 'power_budget', (TType.STRING, 'UTF8', TType.DOUBLE, None, False), None, ),  # 8
    (9, TType.MAP, 'cost_budget', (TType.STRING, 'UTF8', TType.DOUBLE, None, False), None, ),  # 9
)
all_structs.append(SubobjectiveDetails)
SubobjectiveDetails.thrift_spec = (
    None,  # 0
    (1, TType.STRING, 'param', 'UTF8', None, ),  # 1
    (2, TType.LIST, 'attr_names', (TType.STRING, 'UTF8', False), None, ),  # 2
    (3, TType.LIST, 'attr_values', (TType.LIST, (TType.STRING, 'UTF8', False), False), None, ),  # 3
    (4, TType.LIST, 'scores', (TType.DOUBLE, None, False), None, ),  # 4
    (5, TType.LIST, 'taken_by', (TType.STRING, 'UTF8', False), None, ),  # 5
    (6, TType.LIST, 'justifications', (TType.LIST, (TType.STRING, 'UTF8', False), False), None, ),  # 6
)
fix_spec(all_structs)
del all_structs
