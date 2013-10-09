__author__ = 'yiqingj'

from map import vector_pb2

area = vector_pb2.AreaFeature()
ring = area.rings.add()
featName = area.areaNames.add()
featName.name = 'featurename'
featName.alias = 'alias'
area.name = 'name'
area.featureID = 100
area.subType = 'road'
f = open('test.pb',"wb")
f.write(area.SerializeToString())
f.close();

