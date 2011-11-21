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

from datetime import datetime
from xml.dom.minidom import parse

from nens import fews

from timeseries.timeseries import TimeSeries
from timeseries.timeseriesstub import write_to_pi_file

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
        'maximum_level': 'MARG_BOV',
        'minimum_level': 'MARG_OND',
        'nutricalc_incr': '',
        'nutricalc_min': '',
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

LABEL2PARAMETER = {
    'drained': 'discharge_drained',
    'evaporation': 'evaporation',
    'flow_off': 'discharge_flow_off',
    'hardened': 'discharge_hardened',
    'indraft': 'indraft',
    'infiltration': ' infiltration',
    'precipitation': 'precipitation',
    'seepage': 'seepage',
    'sluice_error': 'sluice_error',
    'undrained': 'discharge_drainage',
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

class TimeseriesFactory(object):

    @classmethod
    def create(self, area, label2parameter, label2timeseries):
        multiple_timeseries = []
        for label, timeseries in label2timeseries.iteritems():
            if type(label) == str:
                if label in label2parameter.iterkeys():
                    multiple_timeseries.append(TimeseriesForLabel(timeseries,
                                                                  area.location_id,
                                                                  label2parameter[label]))
            else:
                station = label
                multiple_timeseries.append(TimeseriesForPumpingStation(timeseries,
                                                                       station.location_id))
        return multiple_timeseries

class TimeseriesForLabel(object):

    def __init__(self, timeseries, location_id, parameter_id):
        self.timeseries = timeseries
        self.location_id = location_id
        self.parameter_id = parameter_id

    def set_fields(self):
        self.timeseries.location_id = self.location_id
        self.timeseries.parameter_id = self.parameter_id
        self.set_timeseries_fields()

    def set_timeseries_fields(self):
        self.timeseries.type = 'instantaneous'
        self.timeseries.miss_val = '-999.0'
        self.timeseries.station_name = 'Huh?'
        self.timeseries.units = 'dag'

class TimeseriesForPumpingStation(object):

    def __init__(self, timeseries, location_id):
        self.timeseries = timeseries
        self.location_id = location_id

    def set_fields(self):
        self.timeseries.location_id = self.location_id
        self.timeseries.parameter_id = 'Q'
        self.set_timeseries_fields()

    def set_timeseries_fields(self):
        self.timeseries.type = 'instantaneous'
        self.timeseries.miss_val = '-999.0'
        self.timeseries.station_name = 'Huh?'
        self.timeseries.units = 'dag'


class WriteableTimeseries(object):

    def __init__(self, area, label2parameter):
        self.area = area
        self.label2parameter = label2parameter
        self.timeseries_list = []

    def insert(self, label2timeseries):

        multiple_timeseries = TimeseriesFactory.create(self.area, self.label2parameter, label2timeseries)
        for timeseries in multiple_timeseries:
            timeseries.set_fields()
            self.timeseries_list.append(timeseries.timeseries)

    def insert2(self, station2timeseries):

        multiple_timeseries = TimeseriesFactory.create(self.area, self.label2parameter, station2timeseries)
        for timeseries in multiple_timeseries:
            timeseries.set_fields()
            self.timeseries_list.append(timeseries.timeseries)


def store_graphs_timeseries(run_info, area, graphs_timeseries):

    cm = WaterbalanceComputer2(None, area)

    # print run_info
    start_date, end_date = run_info["startDateTime"], run_info["endDateTime"]
    incoming = cm.get_open_water_incoming_flows(start_date, end_date)
    # outgoing = cm.get_open_water_outgoing_flows(start_date, end_date)
    # sluice_error = cm.calc_sluice_error_timeseries(start_date, end_date)

    timeseries_writer = WriteableTimeseriesCreator(area, LABEL2PARAMETER)

    timeseries_writer.insert(incoming)
    # timeseries_dict.insert(outgoing, parameter2timeseries)
    # timeseries_dict.insert({'sluice_error':sluice_error}, parameter2timeseries)


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
    log.debug(run_info['inputTimeSeriesFile'])
    tsd = TimeSeries.as_dict(run_info['inputTimeSeriesFile'])
    area = parse_parameters(run_info['inputParameterFile'])
    attach_timeseries_to_structures(area, tsd, ASSOC)
    graphs_timeseries = []
    store_graphs_timeseries(run_info, area, graphs_timeseries)
    TimeSeries.write_to_pi_file(run_info['outputTimeSeriesFile'],
                                graphs_timeseries)
