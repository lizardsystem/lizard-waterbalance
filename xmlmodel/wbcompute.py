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
from timeseries.timeseriesstub import enumerate_events

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
        'water_level': 'WATHTE',
        },
    'Bucket': {
        # note that this is net seepage, so seepage minus infiltration
        'seepage': 'KWEL',
        'sewer': 'Qoverstort',
        },
    'PumpingStation': {
        'sum_timeseries': 'Q',
        },
    }


class Units(object):
    """Specifies the different units for each flow type.

    These units are implemented as class variables to mimic global definitions.

    """
    concentration = 'g/m3'
    flow = 'm3/dag'
    fraction = '[0,1]'
    impact = 'mg/m2/dag'
    level = 'mNAP'
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
    'water_level': \
        TimeSeriesSpec('water_level', Units.level),
    'sluice_error': \
        TimeSeriesSpec('sluice_error', Units.flow),
    'undrained': \
        TimeSeriesSpec('discharge_drainage', Units.flow),
    'sewer': \
        TimeSeriesSpec('discharge_sewer', Units.flow),
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
    'min_impact_phosphate_level_control': \
        TimeSeriesSpec('min_impact_phosphate_level_control', Units.impact),
    'incr_impact_phosphate_level_control': \
        TimeSeriesSpec('incr_impact_phosphate_level_control', Units.impact),
    'min_impact_nitrogen_level_control': \
        TimeSeriesSpec('min_impact_nitrogen_level_control', Units.impact),
    'incr_impact_nitrogen_level_control': \
        TimeSeriesSpec('incr_impact_nitrogen_level_control', Units.impact),
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
    'min_impact_sulphate_precipitation': \
        TimeSeriesSpec('min_impact_sulphate_precipitation', Units.impact),
    'min_impact_sulphate_seepage': \
        TimeSeriesSpec('min_impact_sulphate_seepage', Units.impact),
    'incr_impact_sulphate_precipitation': \
        TimeSeriesSpec('incr_impact_sulphate_precipitation', Units.impact),
    'incr_impact_sulphate_seepage': \
        TimeSeriesSpec('incr_impact_sulphate_seepage', Units.impact),
    'min_impact_sulphate_discharge': \
        TimeSeriesSpec('min_impact_sulphate_discharge', Units.impact),
    'incr_impact_sulphate_discharge': \
        TimeSeriesSpec('incr_impact_sulphate_discharge', Units.impact),
    'min_impact_sulphate_level_control': \
        TimeSeriesSpec('min_impact_sulphate_level_control', Units.impact),
    'incr_impact_sulphate_level_control': \
        TimeSeriesSpec('incr_impact_sulphate_level_control', Units.impact),
    'min_impact_sulphate_hardened': \
        TimeSeriesSpec('min_impact_sulphate_hardened', Units.impact),
    'incr_impact_sulphate_hardened': \
        TimeSeriesSpec('incr_impact_sulphate_hardened', Units.impact),
    'min_impact_sulphate_drained': \
        TimeSeriesSpec('min_impact_sulphate_drained', Units.impact),
    'incr_impact_sulphate_drained': \
        TimeSeriesSpec('incr_impact_sulphate_drained', Units.impact),
    'min_impact_sulphate_undrained': \
        TimeSeriesSpec('min_impact_sulphate_drainage', Units.impact),
    'incr_impact_sulphate_undrained': \
        TimeSeriesSpec('incr_impact_sulphate_drainage', Units.impact),
    'min_impact_sulphate_flow_off': \
        TimeSeriesSpec('min_impact_sulphate_flow_off', Units.impact),
    'incr_impact_sulphate_flow_off': \
        TimeSeriesSpec('incr_impact_sulphate_flow_off', Units.impact),
    'min_impact_sulphate_sewer': \
        TimeSeriesSpec('min_impact_sulphate_sewer', Units.impact),
    'incr_impact_sulphate_sewer': \
        TimeSeriesSpec('incr_impact_sulphate_sewer', Units.impact),
    'concentrations': \
        TimeSeriesSpec('chloride', Units.concentration),
    'delta_storage': \
        TimeSeriesSpec('delta_storage', Units.storage),
    'fraction_initial': \
        TimeSeriesSpec('fraction_water_initial', Units.fraction),
    'fraction_precipitation': \
        TimeSeriesSpec('fraction_water_precipitation', Units.fraction),
    'fraction_seepage': \
        TimeSeriesSpec('fraction_water_seepage', Units.fraction),
    'fraction_hardened': \
        TimeSeriesSpec('fraction_water_hardened', Units.fraction),
    'fraction_drained': \
        TimeSeriesSpec('fraction_water_drained', Units.fraction),
    'fraction_undrained': \
        TimeSeriesSpec('fraction_water_drainage', Units.fraction),
    'fraction_flow_off': \
        TimeSeriesSpec('fraction_water_flow_off', Units.fraction),
    'fraction_sewer': \
        TimeSeriesSpec('fraction_water_sewer', Units.fraction),
    'fraction_discharge': \
        TimeSeriesSpec('fraction_water_discharge', Units.fraction),
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

    def __eq__(self, other):
        return self.timeseries == other.timeseries and \
            self.location_id == other.location_id and \
            self.parameter_id == other.parameter_id and \
            self.units == other.units


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
        writeables = TimeseriesForSomething.create(self.area,
            self.label2time_series_spec, mapping2timeseries)
        self.append_writeables(writeables)

    def append_writeables(self, writeables):
        for writeable in writeables:
            writeable.set_standard_fields()
            writeable.set_specific_fields()
            self.timeseries_list.append(writeable.timeseries)

class FractionsTimeseries(object):

    def __init__(self, area_id):
        self.area_id = area_id

    def as_writeables(self, label2values):
        """Return the fraction time series as a list of writeable TimeSeries.

        Parameter:
          *label2values*
            dict of (string) label to a value that is either (i) a
            dict of intake to fraction time series when the label is equal
            to 'intakes', or (ii) a single fraction time series when
            otherwise

        """
        writeables = []
        for label, values in label2values.items():
            if label == 'intakes':
                # values is a dict of intake to single fraction time series
                writeables += self._as_writeables_for_intakes(values)
            else:
                # values is a single fraction time series
                writeable = self._create_writeable(values, self.area_id,
                                                   'fraction_water_' + label)
                writeables.append(writeable)
        return writeables

    def _as_writeables_for_intakes(self, intake2timeseries):
        writeables = []
        for intake, timeseries in intake2timeseries.items():
            if intake.is_computed:
                parameter = 'fraction_water_level_control'
            else:
                parameter = 'fraction_water_discharge'
            writeable = self._create_writeable(timeseries, intake.location_id,
                                               parameter)
            writeables.append(writeable)
        return writeables

    def _create_writeable(self, timeseries, location, parameter):
        units = Units.fraction
        return TimeseriesForLabel(timeseries, location, parameter, units)

def store_graphs_timeseries(run_info, area):

    cm = WaterbalanceComputer2(None, area)

    start_date, end_date = run_info["startDateTime"], run_info["endDateTime"]
    incoming = cm.get_open_water_incoming_flows(start_date, end_date)
    outgoing = cm.get_open_water_outgoing_flows(start_date, end_date)
    water_level, sluice_error = cm.get_waterlevel_with_sluice_error(start_date, end_date)

    writeable_timeseries = WriteableTimeseriesList(area, LABEL2TIMESERIESSPEC)

    writeable_timeseries.insert(incoming)
    writeable_timeseries.insert(outgoing)
    writeable_timeseries.insert({'water_level': water_level})
    writeable_timeseries.insert({'sluice_error': sluice_error})

    for substance in ['phosphate', 'nitrogen', 'sulphate']:
        impacts, impacts_incremental = \
            cm.get_impact_timeseries(start_date, end_date, substance)

        for (impact, impact_incremental) in zip(impacts, impacts_incremental):
             assert impact.label == impact_incremental.label
             if type(impact) == LoadForIntake:
                 if impact.label.is_computed:
                     name = 'level_control'
                 else:
                     name = 'discharge'
                 label = '%s_impact_%s_%s' % ('min', substance, name)
                 writeable_timeseries.insert({'intakes': (label, {impact.label: impact.timeseries})})
                 label = '%s_impact_%s_%s' % ('incr', substance, name)
                 writeable_timeseries.insert({'intakes': (label, {impact_incremental.label: impact_incremental.timeseries})})
             else:
                 key = '%s_impact_%s_%s' % ('min', substance, impact.label)
                 writeable_timeseries.insert({key: impact.timeseries})
                 key = '%s_impact_%s_%s' % ('incr', substance, impact.label)
                 writeable_timeseries.insert({key: impact_incremental.timeseries})

    storage_timeseries = StorageTimeseries(cm)
    get_storage_timeseries = storage_timeseries.get
    get_delta_storage = storage_timeseries.get_delta_storage
    timeseries = DeltaStorage(get_storage_timeseries, get_delta_storage).compute(start_date, end_date)
    writeable_timeseries.insert({'delta_storage': timeseries})

    concentrations = cm.get_concentration_timeseries(start_date, end_date)
    writeable_timeseries.insert({'concentrations': concentrations})

    fractions = cm.get_fraction_timeseries(start_date, end_date)
    writeables = FractionsTimeseries(area.location_id).as_writeables(fractions)
    writeable_timeseries.append_writeables(writeables)

    return writeable_timeseries.timeseries_list

class StorageTimeseries(object):

    def __init__(self, wb_computer):
        self.wb_computer = wb_computer

    def get(self, start_date, end_date):
        self.timeseries_dict = \
            self.wb_computer.get_level_control_timeseries(start_date, end_date)
        return self.timeseries_dict['storage']

    def get_delta_storage(self, latest_date):
        incoming_timeseries = self.timeseries_dict['total_incoming']
        outgoing_timeseries = self.timeseries_dict['total_outgoing']
        delta_storage = 0.0
        for events in enumerate_events(incoming_timeseries, outgoing_timeseries):
            date = events[0][0]
            if date.isocalendar() > latest_date.isocalendar():
                break
            else:
                incoming, outgoing = events[0][1], events[1][1]
                delta_storage = incoming + outgoing
        return delta_storage


def negate_outgoing_timeseries(area):
    """Make the sign of the time series of pumps negative.

    The XML specifies the time series for the pumping stations. Their event
    values are always non-negative, even if the pumping station pumps water out
    of the open water. But the computational core expects the event values of
    outgoing time series to be non-positive. So we make these event values
    non-positive.

    """
    for ps in area.pumping_stations:
        if not ps.into:
            ps.sum_timeseries = abs(ps.sum_timeseries) * -1.0


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
    negate_outgoing_timeseries(area)
    graphs_timeseries = store_graphs_timeseries(run_info, area)
    TimeSeries.write_to_pi_file(run_info['outputTimeSeriesFile'],
                                graphs_timeseries)

if __name__ == '__main__':

    main(sys.argv[1:])
