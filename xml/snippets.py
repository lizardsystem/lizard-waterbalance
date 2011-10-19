#!/usr/bin/python

from xml.dom.minidom import Document, parse
d = parse("/home/mario/Tickets/3350/Modules/Waterbalans/Waterbalans/input/Parameter.xml")
rootNode = d.childNodes[0]
groupNodes = [i for i in rootNode.childNodes if i.nodeType != i.TEXT_NODE]

g = []
for group in groupNodes:
    obj = {}
    for parameter in group.getElementsByTagName("parameter"):
        included_elements = [i for i in parameter.childNodes if i.nodeType != i.TEXT_NODE]

        p = {'id': parameter.attributes['id'].value,
             'name': parameter.attributes['name'].value,
             'desc': included_elements[0].childNodes[0].nodeValue
             }
        
        if parameter.getElementsByTagName("stringValue"):
            p['type'] = str
        elif parameter.getElementsByTagName("dblValue"):
            p['type'] = float
        elif parameter.getElementsByTagName("boolValue"):
            p['type'] = bool

        p['value'] = p['type'](included_elements[1].childNodes[0].nodeValue)
        obj[p['id']] = p

    g.append(obj)

print g
