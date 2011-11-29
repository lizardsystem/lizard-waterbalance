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
# initial version:    2011-11-08
#
#******************************************************************************

import logging
import sys

from datetime import datetime
from xml.dom.minidom import parse

from nens import fews

from timeseries.timeseries import TimeSeries

from lizard_wbcomputation.compute import WaterbalanceComputer2
from xmlmodel.reader import parse_parameters
from xmlmodel.reader import attach_timeseries_to_structures


log = logging.getLogger(__name__)

def getText(node):
    return str("".join(t.nodeValue for t in node.childNodes
                       if t.nodeType == t.TEXT_NODE))


ASSOC = {
    'Area': {
        'evaporation': 'VERDPG',
        'infiltration': 'WEGZ',
        'maximum_level': 'WATHTE.boven',
        'minimum_level': 'WATHTE.onder',
        'nutricalc_incr': 'NUTRIC_INC',
        'nutricalc_min': 'NUTRIC_MIN',
        'precipitation': 'NEERSG',
        'seepage': 'KWEL',
        'sewer': '',
        'water_level': 'WATHTE',
        },
    'Bucket': {
        # note that this is net seepage, so seepage minus infiltration
        'seepage': 'KWEL',
        },
    'PumpingStation': {
        'sum_timeseries': 'Q',
        },
    }


class TimeSeriesSpec(object):
    """Specifies TimeSeries attributes.

    A TimeSeries has several attributes that have to be set for a TimeSeries to
    be valid. A TimeSeriesSpec specifies specific values for these attributes.

    """

    def __init__(self, parameter_id, units):
        self.parameter_id = parameter_id
        self.units = units


LABEL2PARAMETER = {
    'drained': TimeSeriesSpec('discharge_drained', 'm3/dag'),
    'evaporation': TimeSeriesSpec('evaporation', 'm3/dag'),
    'flow_off': TimeSeriesSpec('discharge_flow_off', 'm3/dag'),
    'hardened': TimeSeriesSpec('discharge_hardened', 'm3/dag'),
    'indraft': TimeSeriesSpec('indraft', 'm3/dag'),
    'infiltration': TimeSeriesSpec('infiltration', 'm3/dag'),
    'precipitation': TimeSeriesSpec('precipitation', 'm3/dag'),
    'seepage': TimeSeriesSpec('seepage', 'm3/dag'),
    'sluice_error': TimeSeriesSpec('sluice_error', 'm3/dag'),
    'undrained': TimeSeriesSpec('discharge_drainage', 'm3/dag'),
    'min_impact_phosphate_precipitation': TimeSeriesSpec('min_impact_phosphate_precipitation', 'm3/dag'),
    'min_impact_phosphate_seepage': TimeSeriesSpec('min_impact_phosphate_seepage', 'm3/dag'),
    'incr_impact_phosphate_precipitation': TimeSeriesSpec('incr_impact_phosphate_precipitation', 'm3/dag'),
    'incr_impact_phosphate_seepage': TimeSeriesSpec('incr_impact_phosphate_seepage', 'm3/dag'),
    'min_impact_nitrogen_precipitation': TimeSeriesSpec('min_impact_nitrogen_precipitation', 'm3/dag'),
    'min_impact_nitrogen_seepage': TimeSeriesSpec('min_impact_nitrogen_seepage', 'm3/dag'),
    'incr_impact_nitrogen_precipitation': TimeSeriesSpec('incr_impact_nitrogen_precipitation', 'm3/dag'),
    'incr_impact_nitrogen_seepage': TimeSeriesSpec('incr_impact_nitrogen_seepage', 'm3/dag'),
    }


def insert_calculation_range(run_dom, run_info):
    """Insert the calculation start and end datetime into the given dict.

    The start date will be accessible through key 'startDateTime', the end date through
    key 'endDateTime'.

    """
    def get_datetime_string(run_dom, datetime_tag):
        element = run_dom.getElementsByTagName(datetime_tag)[0]
        return element.getAttribute('date') + ' ' + element.getAttribute('time')

    def insert_datetime(run_dom, datetime_tag, run_info):
        datetime_string = get_datetime_string(run_dom, datetime_tag)
        run_info[datetime_tag] = \
            datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')

    insert_datetime(run_dom, 'startDateTime', run_info)
    insert_datetime(run_dom, 'endDateTime', run_info)


class TimeseriesForSomething(object):

    @classmethod
    def create(cls, area, label2parameter, mapping2timeseries):
        multiple_timeseries = []
        for key, timeseries in mapping2timeseries.iteritems():
            if type(key) == str:
                label = key
                if label in label2parameter.keys():
                    spec = label2parameter[label]
                    multiple_timeseries.append(TimeseriesForLabel(timeseries,
                                                                  area.location_id,
                                                                  spec.parameter_id,
                                                                  spec.units))
            else:
                station = key
                multiple_timeseries.append(TimeseriesForPumpingStation(timeseries,
                                                                       station.location_id))
        return multiple_timeseries

    def set_standard_fields(self):
        self.timeseries.type = 'instantaneous'
        self.timeseries.miss_val = '-999.0'
        self.timeseries.station_name = 'Huh?'


class TimeseriesForLabel(TimeseriesForSomething):

    def __init__(self, timeseries, location_id, parameter_id, units):
        self.timeseries = timeseries
        self.location_id = location_id
        self.parameter_id = parameter_id
        self.units = units

    def set_specific_fields(self):
        self.timeseries.location_id = self.location_id
        self.timeseries.parameter_id = self.parameter_id
        self.timeseries.units = self.units


class TimeseriesForPumpingStation(TimeseriesForSomething):

    def __init__(self, timeseries, location_id):
        self.timeseries = timeseries
        self.location_id = location_id

    def set_specific_fields(self):
        self.timeseries.location_id = self.location_id
        self.timeseries.parameter_id = 'Q'
        self.timeseries.units = 'm3/dag'


class WriteableTimeseriesList(object):

    def __init__(self, area, label2parameter):
        self.area = area
        self.label2parameter = label2parameter
        self.timeseries_list = []

    def insert(self, mapping2timeseries):
        multiple_timeseries = TimeseriesForSomething.create(self.area,
            self.label2parameter, mapping2timeseries)
        for timeseries in multiple_timeseries:
            timeseries.set_standard_fields()
            timeseries.set_specific_fields()
            self.timeseries_list.append(timeseries.timeseries)


def store_graphs_timeseries(run_info, area):

    cm = WaterbalanceComputer2(None, area)

    start_date, end_date = run_info["startDateTime"], run_info["endDateTime"]
    incoming = cm.get_open_water_incoming_flows(start_date, end_date)
    outgoing = cm.get_open_water_outgoing_flows(start_date, end_date)
    sluice_error = cm.calc_sluice_error_timeseries(start_date, end_date)

    writeable_timeseries = WriteableTimeseriesList(area, LABEL2PARAMETER)

    writeable_timeseries.insert(incoming)
    writeable_timeseries.insert(outgoing)
    writeable_timeseries.insert({'sluice_error':sluice_error})

    for substance in ['phosphate', 'nitrogen']:
        impact_series, impact_incremental_series = \
            cm.get_impact_timeseries(start_date, end_date, substance)
        for flow in ['precipitation', 'seepage']:
            key = '%s_impact_%s_%s' % ('min', substance, flow)
            writeable_timeseries.insert({key: impact_series[flow]})
            key = '%s_impact_%s_%s' % ('incr', substance, flow)
            writeable_timeseries.insert({key: impact_incremental_series[flow]})

    return writeable_timeseries.timeseries_list

def main(args):
    """Compute the waterbalance for the information specified in the given file.

    This function accepts a single parameter, viz. the file path to the Run.xml
    file that specifies all the other required files.

    """
    run_file, = args
    run_dom = parse(run_file)
    root = run_dom.childNodes[0]
    run_info = dict([(i.tagName, getText(i))
                     for i in root.childNodes
                     if i.nodeType != i.TEXT_NODE
                     and i.tagName != u"properties"])
    insert_calculation_range(run_dom, run_info)
    diag = fews.DiagHandler(run_info['outputDiagnosticFile'])
    logging.getLogger().addHandler(diag)
    logging.getLogger().setLevel(logging.DEBUG)
    log.debug(run_info['inputTimeSeriesFile'])
    tsd = TimeSeries.as_dict(run_info['inputTimeSeriesFile'])
    area = parse_parameters(run_info['inputParameterFile'])
    attach_timeseries_to_structures(area, tsd, ASSOC)
    graphs_timeseries = store_graphs_timeseries(run_info, area)
    TimeSeries.write_to_pi_file(run_info['outputTimeSeriesFile'],
                                graphs_timeseries)

if __name__ == '__main__':

    main(sys.argv[1:])
