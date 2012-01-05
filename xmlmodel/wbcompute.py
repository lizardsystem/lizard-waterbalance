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
from lizard_wbcomputation.delta_storage import DeltaStorage
from lizard_wbcomputation.load_computer import LoadForIntake

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


class Units(object):
    """Specifies the different units for each flow type.

    These units are implemented as class variables to mimic global definitions.

    """
    flow = 'm3/dag'
    impact = 'mg/m2/dag'
    storage = 'm3'


class TimeSeriesSpec(object):
    """Specifies TimeSeries attributes.

    A TimeSeries has several attributes that have to be set for a TimeSeries to
    be valid. A TimeSeriesSpec specifies these attributes for a single
    TimeSeries.

    """

    def __init__(self, parameter_id, units):
        self.parameter_id = parameter_id
        self.units = units


LABEL2TIMESERIESSPEC = {
    'drained': \
        TimeSeriesSpec('discharge_drained', Units.flow),
    'evaporation': \
        TimeSeriesSpec('evaporation', Units.flow),
    'flow_off': \
        TimeSeriesSpec('discharge_flow_off', Units.flow),
    'hardened': \
        TimeSeriesSpec('discharge_hardened', Units.flow),
    'indraft': \
        TimeSeriesSpec('indraft', Units.flow),
    'infiltration': \
        TimeSeriesSpec('infiltration', Units.flow),
    'precipitation': \
        TimeSeriesSpec('precipitation', Units.flow),
    'seepage': \
        TimeSeriesSpec('seepage', Units.flow),
    'sluice_error': \
        TimeSeriesSpec('sluice_error', Units.flow),
    'undrained': \
        TimeSeriesSpec('discharge_drainage', Units.flow),
    'min_impact_phosphate_precipitation': \
        TimeSeriesSpec('min_impact_phosphate_precipitation', Units.impact),
    'min_impact_phosphate_seepage': \
        TimeSeriesSpec('min_impact_phosphate_seepage', Units.impact),
    'incr_impact_phosphate_precipitation': \
        TimeSeriesSpec('incr_impact_phosphate_precipitation', Units.impact),
    'incr_impact_phosphate_seepage': \
        TimeSeriesSpec('incr_impact_phosphate_seepage', Units.impact),
    'min_impact_nitrogen_precipitation': \
        TimeSeriesSpec('min_impact_nitrogen_precipitation', Units.impact),
    'min_impact_nitrogen_seepage': \
        TimeSeriesSpec('min_impact_nitrogen_seepage', Units.impact),
    'incr_impact_nitrogen_precipitation': \
        TimeSeriesSpec('incr_impact_nitrogen_precipitation', Units.impact),
    'incr_impact_nitrogen_seepage': \
        TimeSeriesSpec('incr_impact_nitrogen_seepage', Units.impact),
    'min_impact_phosphate_discharge': \
        TimeSeriesSpec('min_impact_phosphate_discharge', Units.impact),
    'incr_impact_phosphate_discharge': \
        TimeSeriesSpec('incr_impact_phosphate_discharge', Units.impact),
    'min_impact_nitrogen_discharge': \
        TimeSeriesSpec('min_impact_nitrogen_discharge', Units.impact),
    'incr_impact_nitrogen_discharge': \
        TimeSeriesSpec('incr_impact_nitrogen_discharge', Units.impact),
    'min_impact_phosphate_hardened': \
        TimeSeriesSpec('min_impact_phosphate_hardened', Units.impact),
    'incr_impact_phosphate_hardened': \
        TimeSeriesSpec('incr_impact_phosphate_hardened', Units.impact),
    'min_impact_nitrogen_hardened': \
        TimeSeriesSpec('min_impact_nitrogen_hardened', Units.impact),
    'incr_impact_nitrogen_hardened': \
        TimeSeriesSpec('incr_impact_nitrogen_hardened', Units.impact),
    'min_impact_phosphate_drained': \
        TimeSeriesSpec('min_impact_phosphate_drained', Units.impact),
    'incr_impact_phosphate_drained': \
        TimeSeriesSpec('incr_impact_phosphate_drained', Units.impact),
    'min_impact_nitrogen_drained': \
        TimeSeriesSpec('min_impact_nitrogen_drained', Units.impact),
    'incr_impact_nitrogen_drained': \
        TimeSeriesSpec('incr_impact_nitrogen_drained', Units.impact),
    'min_impact_phosphate_undrained': \
        TimeSeriesSpec('min_impact_phosphate_drainage', Units.impact),
    'incr_impact_phosphate_undrained': \
        TimeSeriesSpec('incr_impact_phosphate_drainage', Units.impact),
    'min_impact_nitrogen_undrained': \
        TimeSeriesSpec('min_impact_nitrogen_drainage', Units.impact),
    'incr_impact_nitrogen_undrained': \
        TimeSeriesSpec('incr_impact_nitrogen_drainage', Units.impact),
    'min_impact_phosphate_flow_off': \
        TimeSeriesSpec('min_impact_phosphate_flow_off', Units.impact),
    'incr_impact_phosphate_flow_off': \
        TimeSeriesSpec('incr_impact_phosphate_flow_off', Units.impact),
    'min_impact_nitrogen_flow_off': \
        TimeSeriesSpec('min_impact_nitrogen_flow_off', Units.impact),
    'incr_impact_nitrogen_flow_off': \
        TimeSeriesSpec('incr_impact_nitrogen_flow_off', Units.impact),
    'min_impact_phosphate_sewer': \
        TimeSeriesSpec('min_impact_phosphate_sewer', Units.impact),
    'incr_impact_phosphate_sewer': \
        TimeSeriesSpec('incr_impact_phosphate_sewer', Units.impact),
    'min_impact_nitrogen_sewer': \
        TimeSeriesSpec('min_impact_nitrogen_sewer', Units.impact),
    'incr_impact_nitrogen_sewer': \
        TimeSeriesSpec('incr_impact_nitrogen_sewer', Units.impact),
    'delta_storage': \
        TimeSeriesSpec('delta_storage', Units.storage),
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
    def create(cls, area, label2time_series_spec, mapping2timeseries):
        multiple_timeseries = []
        sorted_elements = mapping2timeseries.items()
        sorted_elements.sort(key=lambda e:e[0])
        for key, timeseries in sorted_elements:
            assert type(key) == str
            if key == 'intakes':
                label, intake2timeseries = timeseries
                if label in label2time_series_spec.keys():
                    spec = label2time_series_spec[label]
                    for intake, ts in intake2timeseries.iteritems():
                        multiple_timeseries.append(TimeseriesForLabel(ts,
                                                                      intake.location_id,
                                                                      spec.parameter_id,
                                                                      spec.units))
            elif key in ['defined_input', 'defined_output']:
                for station, station_timeseries in timeseries.items():
                    multiple_timeseries.append(TimeseriesForPumpingStation(station_timeseries,
                                                                           station.location_id))
            elif key in ['intake_wl_control', 'outtake_wl_control']:
                for station, station_timeseries in timeseries.items():
                    multiple_timeseries.append(TimeseriesForLabel(station_timeseries,
                                                                  station.location_id,
                                                                  'Q_COMP',
                                                                  Units.flow))
            else:
                label = key
                if label in label2time_series_spec.keys():
                    spec = label2time_series_spec[label]
                    multiple_timeseries.append(TimeseriesForLabel(timeseries,
                                                                  area.location_id,
                                                                  spec.parameter_id,
                                                                  spec.units))

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
        self.timeseries.units = Units.flow


class WriteableTimeseriesList(object):

    def __init__(self, area, label2time_series_spec):
        self.area = area
        self.label2time_series_spec = label2time_series_spec
        self.timeseries_list = []

    def insert(self, mapping2timeseries):
        multiple_timeseries = TimeseriesForSomething.create(self.area,
            self.label2time_series_spec, mapping2timeseries)
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

    writeable_timeseries = WriteableTimeseriesList(area, LABEL2TIMESERIESSPEC)

    writeable_timeseries.insert(incoming)
    writeable_timeseries.insert(outgoing)
    writeable_timeseries.insert({'sluice_error':sluice_error})

    for substance in ['phosphate', 'nitrogen']:
        impacts, impacts_incremental = \
            cm.get_impact_timeseries(start_date, end_date, substance)

        for (impact, impact_incremental) in zip(impacts, impacts_incremental):
             assert impact.label == impact_incremental.label
             if type(impact) == LoadForIntake:
                 label = '%s_impact_%s_discharge' % ('min', substance)
                 writeable_timeseries.insert({'intakes': (label, {impact.label: impact.timeseries})})
                 label = '%s_impact_%s_discharge' % ('incr', substance)
                 writeable_timeseries.insert({'intakes': (label, {impact_incremental.label: impact_incremental.timeseries})})
             else:
                 key = '%s_impact_%s_%s' % ('min', substance, impact.label)
                 print key
                 writeable_timeseries.insert({key: impact.timeseries})
                 key = '%s_impact_%s_%s' % ('incr', substance, impact.label)
                 writeable_timeseries.insert({key: impact_incremental.timeseries})

    get_storage_timeseries = StorageTimeseries(cm).get
    timeseries = DeltaStorage(get_storage_timeseries).compute(start_date, end_date)
    writeable_timeseries.insert({'delta_storage': timeseries})

    return writeable_timeseries.timeseries_list

class StorageTimeseries(object):

    def __init__(self, wb_computer):
        self.wb_computer = wb_computer

    def get(self, start_date, end_date):
        timeseries_dict = \
            self.wb_computer.get_level_control_timeseries(start_date, end_date)
        return timeseries_dict['storage']

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
