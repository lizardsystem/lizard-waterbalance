#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2011 Nelen & Schuurmans
#
#******************************************************************************
#
# initial programmer: Mario Frasca
# initial version:    2011-10-19
#
#******************************************************************************

import uuid
import logging
import datetime

logger = logging.getLogger(__name__)

from timeseries.timeseries import TimeSeries


class BaseModel(object):
    expected = ['obj_id', 'location_id']
    def __init__(self):
        self.obj_id = str(uuid.uuid4())
        self.location_id = "<NO_LOC>"
        self.timeseries_names = set()

    def __eq__(self, other):
        """two objects are equal iff they have the same hash and their
        atomic attributes are equal
        """

        return reduce(lambda x, y: x and y,
                      [getattr(self, a, None) == getattr(other, a, None)
                       for a in set(dir(self)).union(dir(other))
                       if type(getattr(self, a, None)) in (bool, str, float)],
                      hash(self) == hash(other))

    def __str__(self):
        return "%s:%s/%s" % (self.__class__.__name__, self.obj_id, self.location_id)

    def __hash__(self):
        return hash(str(self))

    def __getattr__(self, attr):

        if attr.startswith("retrieve_"):
            name = attr[len("retrieve_"):]
            if name in self.timeseries_names:
                timeseries = getattr(self, name)
                return (lambda start=None, end=None:
                            timeseries.filter(timestamp_gte=start, timestamp_lte=end))
        return getattr(super(BaseModel, self), attr)

    def validate(self):
        """check whether self contains all expected fields

        when your are done adding attributes to object, invoke this
        function.  it will return True if things went ok, otherwise
        something else.

        for all missing but expected attributes a WARNING logging
        record will be passed to the module logger.
        """

        valid = True
        for field in self.expected:
            if not hasattr(self, field):
                logger.warn("%s has no %s field" % (self, field))
                valid = False
        return valid

    @classmethod
    def corresponding_parameter_id(cls, local_name):
        """return the default parameter id for named timeseries.
        """

        return None


class Area(BaseModel):
    expected = ['obj_id', 'location_id', 'name',
                'surface',
                'bottom_height',
                'ini_con_cl',
                'max_intake',
                'max_outtake',
                'concentr_chloride_precipitation',
                'concentr_chloride_seepage',
                'min_concentr_phosphate_precipitation',
                'incr_concentr_phosphate_precipitation',
                'min_concentr_phosphate_seepage',
                'incr_concentr_phosphate_seepage',
                'min_concentr_nitrogen_precipitation',
                'incr_concentr_nitrogen_precipitation',
                'min_concentr_nitrogen_seepage',
                'incr_concentr_nitrogen_seepage',
                'min_concentr_sulphate_precipitation',
                'incr_concentr_sulphate_precipitation',
                'min_concentr_sulphate_seepage',
                'incr_concentr_sulphate_seepage',
                ]

    def validate(self):
        success = BaseModel.validate(self)
        if success:
            # place additional checks on the validity of the Area data here
            if self.surface < 1e-6:
                logger.warning('area surface of %.1f is too low to handle correctly', self.surface)
                assert False
        return success

    @classmethod
    def corresponding_parameter_id(cls, local_name):
        """return the default parameter id for named timeseries.
        """

        return None

    def set_init_water_level(self, date):
        """Sets the initial water level.

        This method sets the initial water level to the last-known water level
        that is earlier than the given date.

        """
        logger.debug('set initial water level for area %s', self.name)
        self.init_water_level = None
        for event in self.retrieve_water_level().events():
            if event[0] <= date:
                self.init_water_level = event[1]
            else:
                if self.init_water_level is None:
                    s = date.isoformat(' ')
                    logger.warning('no water level known before %s', s)
                    if event[0].isocalendar() == date.isocalendar():
                        self.init_water_level = event[1]
                    else:
                        self.init_water_level = 0.0
                break
        if self.init_water_level is None:
            logger.warning('no water level known')
            self.init_water_level = 0.0
        logger.debug('initial water level of area set to %f',
             self.init_water_level)

    @property
    def init_volume(self):
        water_height = self.init_water_level - self.bottom_height
        if water_height < 0.0:
            logger.warning('initial water level of area %s is below the level of the bottom',
                 self.area.name)
            water_height = 0.0
        return water_height * self.surface

    @property
    def init_concentration(self):
        return self.ini_con_cl

    @property
    def buckets(self):
        return self.bucket

    @property
    def pumping_stations(self):
        return self.pumpingstation


class Bucket(BaseModel):
    expected = ['obj_id', 'location_id',
                'name',
                'surface_type',
                'surface',
                'is_computed',
                'bottom_porosity',
                'crop_evaporation_factor',
                'min_crop_evaporation_factor',
                'bottom_drainage_fraction',
                'bottom_indraft_fraction',
                'bottom_max_water_level',
                'bottom_min_water_level',
                'bottom_equi_water_level',
                'bottom_init_water_level',
                'porosity',
                'drainage_fraction',
                'indraft_fraction',
                'max_water_level',
                'min_water_level',
                'equi_water_level',
                'init_water_level',
                'concentr_chloride_flow_off',
                'concentr_chloride_drainage_indraft',
                'min_concentr_phosphate_flow_off',
                'min_concentr_phosphate_drainage_indraft',
                'incr_concentr_phosphate_flow_off',
                'incr_concentr_phosphate_drainage_indraft',
                'min_concentr_nitrogen_flow_off',
                'min_concentr_nitrogen_drainage_indraft',
                'incr_concentr_nitrogen_flow_off',
                'incr_concentr_nitrogen_drainage_indraft',
                'min_concentr_sulphate_flow_off',
                'min_concentr_sulphate_drainage_indraft',
                'incr_concentr_sulphate_flow_off',
                'incr_concentr_sulphate_drainage_indraft',
                ]

    @classmethod
    def corresponding_parameter_id(cls, local_name):
        """return the default parameter id for named timeseries.
        """

        return None

    pass


class PumpingStation(BaseModel):
    expected = ['obj_id', 'location_id',
                'name',
                'is_computed',
                'into',
                'concentr_chloride',
                'min_concentr_phosphate',
                'incr_concentr_phosphate',
                'min_concentr_nitrogen',
                'incr_concentr_nitrogen',
                'min_concentr_sulphate',
                'incr_concentr_sulphate',
                ]

    @classmethod
    def corresponding_parameter_id(cls, local_name):
        """return the default parameter id for named timeseries.
        """

        return 'Q'

    pass


classes = {'Area': Area,
           'Bucket': Bucket,
           'PumpingStation': PumpingStation,
           }


def parse_parameters(stream):
    r"""parse the xml stream into set of objects

    create as many objects as the `group` elements in the input file.

    each `group` element causes an object needs a `model` element, which
    names the class of the resulting object.

    ====
    the first object in the stream is considered the root of the
    resulting structure.

    >>> from nens.mock import Stream
    >>> type(parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model></group>
    ... </parameters>''')))
    <class 'xmlmodel.reader.Area'>

    ====
    each `parameter` in the `group` cause a field in the resulting
    object, the name of the field is in the `id` attribute of the
    `parameter`, according to whether the `parameter` contains a
    `boolValue`, `dblValue` or a `stringValue`, the field will be a
    boolean, a double or a string, respectively.  the text in the
    element specifies the value of the field.

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="ts_refcl1">
    ... <boolValue>false</boolValue>
    ... </parameter>
    ... </group></parameters>'''))
    >>> root.ts_refcl1
    False

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="max_inl">
    ... <dblValue>144000</dblValue>
    ... </parameter>
    ... </group></parameters>'''))
    >>> root.max_inl
    144000.0

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="geb_naam">
    ... <stringValue>Aetsveldsche polder oost</stringValue>
    ... </parameter>
    ... </group></parameters>'''))
    >>> root.geb_naam
    'Aetsveldsche polder oost'

    ====
    all subsequent objects will be associated to the root, in a field
    named as the class of the object.

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id='obj_id'><stringValue>A1</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L1</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id='obj_id'><stringValue>B1</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L88</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id='obj_id'><stringValue>B2</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L39</stringValue></parameter>
    ... </group><group>
    ... <model>PumpingStation</model>
    ... <parameter id='obj_id'><stringValue>P1</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L130</stringValue></parameter>
    ... </group></parameters>'''))
    >>> len(root.bucket)
    2
    >>> len(root.pumpingstation)
    1
    >>> type(root)
    <class 'xmlmodel.reader.Area'>
    >>> set([type(i) for i in root.bucket])
    set([<class 'xmlmodel.reader.Bucket'>])
    >>> set([type(i) for i in root.pumpingstation])
    set([<class 'xmlmodel.reader.PumpingStation'>])

    what happens if you explicitly convert to string?
    >>> str(root)
    'Area:A1/L1'

    the above representation is used to compute an object's hash!
    >>> hash(root) == hash('Area:A1/L1')
    True

    what happens when you read again the same data?
    will it compare equal to the original?

    if objects have an explicit obj_id, yes:
    >>> root2 = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id='obj_id'><stringValue>A1</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L1</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id='obj_id'><stringValue>B1</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L88</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id='obj_id'><stringValue>B2</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L39</stringValue></parameter>
    ... </group><group>
    ... <model>PumpingStation</model>
    ... <parameter id='obj_id'><stringValue>P1</stringValue></parameter>
    ... <parameter id='location_id'><stringValue>L130</stringValue></parameter>
    ... </group></parameters>'''))
    >>> root == root2
    True
    >>> root.bucket == root2.bucket
    True
    >>> root.pumpingstation == root2.pumpingstation
    True

    you may believe that comparison always returns True?
    >>> root2 == root.bucket[0]
    False
    >>> root.bucket[0] == root.bucket[1]
    False

    if the input file does not explicitly contain obj_id fields, then
    equality is not to be expected.
    >>> root_anon1 = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id='location_id'><stringValue>L1</stringValue></parameter>
    ... </group></parameters>'''))
    >>> root_anon2 = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id='location_id'><stringValue>L1</stringValue></parameter>
    ... </group></parameters>'''))
    >>> root_anon1 == root_anon2
    False

    if you serialize and unserialize an object, equality is retained.
    for example using pickle...
    >>> import pickle
    >>> root_anon1 == pickle.loads(pickle.dumps(root_anon1))
    True

    this means you can use such objects as dictionary keys:
    >>> d = {root: 'found it!'}
    >>> d.get(root2, 'nope')
    'found it!'
    >>> d.get(root.bucket[0], 'nope')
    'nope'

    this is just an example and we miss most expected properties, the
    logger will receive lots of warnings.
    >>> root.validate()
    False
    >>>
    """

    from xml.dom.minidom import parse
    d = parse(stream)
    rootNode = d.childNodes[0]
    groupNodes = [i for i in rootNode.childNodes if i.nodeType != i.TEXT_NODE]

    result = None

    for group in groupNodes:
        models = group.getElementsByTagName("model")
        assert(len(models) == 1)
        for model in models:
            class_name = str(model.childNodes[0].nodeValue)
            this_class = classes[class_name]

        obj = this_class()
        obj.obj_id = str(uuid.uuid4())
        if result is None:
            result = obj
        for parameter in group.getElementsByTagName("parameter"):
            try:
                value_node = parameter.getElementsByTagName("dblValue")[0]
                value = float(value_node.childNodes[0].nodeValue)
            except IndexError:
                try:
                    value_node = parameter.getElementsByTagName("stringValue")[0]
                    value = str(value_node.childNodes[0].nodeValue)
                except IndexError:
                    try:
                        value_node = parameter.getElementsByTagName("boolValue")[0]
                        value = (value_node.childNodes[0].nodeValue).lower().strip() == "true"
                    except IndexError:
                        try:
                            value_node = parameter.getElementsByTagName("intValue")[0]
                            value = int(value_node.childNodes[0].nodeValue)
                        except IndexError:
                            value = None
            setattr(obj, parameter.getAttribute('id'), value)

        obj.validate()

        if obj != result:
            if not hasattr(result, class_name.lower()):
                setattr(result, class_name.lower(), [])
            getattr(result, class_name.lower()).append(obj)

    return result


def attach_timeseries_to_structures(root, tsd, corresponding):
    """couple objects to the corresponding time series.

    root is an object as returned by parse_parameters.

    tsd is a dictionary as returned by timeseries.TimeSeries.as_dict.

    corresponding is a dictionary associating a class name to a
    dictionary associating the expected timeseries with the name as in
    tsd.

    logs names of unused timeseries at info level.
    each unused timeseries causes one log record.

    >>> from nens.mock import Stream
    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="location_id"><stringValue>L1</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id="location_id"><stringValue>B1</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id="location_id"><stringValue>B2</stringValue></parameter>
    ... </group><group>
    ... <model>PumpingStation</model>
    ... <parameter id="location_id"><stringValue>PS1</stringValue></parameter>
    ... </group></parameters>'''))
    >>> tsd = {
    ... ('L1', 'NEERSG'): 1,
    ... ('L1', 'VERDPG'): 2,
    ... ('L1', 'KWEL'): 3,
    ... ('B1', 'NEERSG'): 4,
    ... ('B1', 'VERDPG'): 5,
    ... ('B1', 'KWEL'): 6,
    ... ('B2', 'NEERSG'): 7,
    ... ('B2', 'VERDPG'): 8,
    ... ('B2', 'KWEL'): 9,
    ... ('PS1', 'NEERSG'): 17,
    ... ('PS1', 'VERDPG'): 18,
    ... ('PS1', 'KWEL'): 19,
    ... }
    >>> k = {'Area': {'precipitation': 'NEERSG',
    ...  'evaporation': 'VERDPG',
    ...  'seepage': 'KWEL',
    ...  },
    ... 'Bucket': {'precipitation': 'NEERSG',
    ...  'evaporation': 'VERDPG',
    ...  'seepage': 'KWEL',
    ...  },
    ... 'PumpingStation': {'precipitation': 'NEERSG',
    ...  'evaporation': 'VERDPG',
    ...  'seepage': 'KWEL',
    ...  },
    ... }
    >>> attach_timeseries_to_structures(root, tsd, k) # doctest:+ELLIPSIS
    <xmlmodel.reader.Area object at ...>
    >>> (root.precipitation, root.evaporation, root.seepage)
    (1, 2, 3)
    >>> [(i.precipitation, i.evaporation, i.seepage) for i in root.bucket]
    [(4, 5, 6), (7, 8, 9)]
    >>> [(i.precipitation, i.evaporation, i.seepage) for i in root.pumpingstation]
    [(17, 18, 19)]

    >>> root.retrieve_precipitation # doctest:+ELLIPSIS
    <function <lambda> at ...>
    >>> [i.retrieve_evaporation for i in root.pumpingstation] # doctest:+ELLIPSIS
    [<function <lambda> at ...>]
    """

    available = set(tsd.keys())

    for class_name in corresponding:
        if class_name == root.__class__.__name__:
            todo = [root]
        else:
            todo = getattr(root, class_name.lower())
        for local, remote in corresponding[class_name].items():
            for obj in todo:
                series = tsd.get((obj.location_id, remote))
                if series is None:
                    logger.warn("no series found at loc/par: %s/%s, using empty TimeSeries" %
                                (obj.location_id, remote))
                    series = TimeSeries(location_id=obj.location_id,
                                        parameter_id=obj.corresponding_parameter_id(local))
                available.discard((obj.location_id, remote))
                setattr(obj, local, series)
                obj.timeseries_names.add(local)

    for locpar in sorted(available):
        logger.info("unused series loc/par:  %s/%s" % locpar)
    return root
