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
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************

import logging

from lizard_wbcomputation.bucket_computer import BucketComputer
from lizard_wbcomputation.bucket_summarizer import BucketsSummarizer
from lizard_wbcomputation.concentration_computer import ConcentrationComputer
from lizard_wbcomputation.concentration_computer import ConcentrationComputer2
from lizard_wbcomputation.concentration_computer import TotalVolumeChlorideTimeseries
from lizard_wbcomputation.fraction_computer import FractionComputer
from lizard_wbcomputation.impact_from_buckets import SummaryLoad
from lizard_wbcomputation.impact_from_buckets import SummedLoadsFromBuckets
from lizard_wbcomputation.level_control_assignment import LevelControlAssignment
from lizard_wbcomputation.level_control_computer import DateRange
from lizard_wbcomputation.level_control_computer import LevelControlComputer
from lizard_wbcomputation.load_computer import LoadComputer
from lizard_wbcomputation.memoize import memoize
from lizard_wbcomputation.sluice_error_computer import SluiceErrorComputer
from lizard_wbcomputation.vertical_timeseries_computer import VerticalTimeseriesComputer
from lizard_wbcomputation.export import export_excel_small

from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import SparseTimeseriesStub
from timeseries.timeseriesstub import TimeseriesRestrictedStub

logger = logging.getLogger(__name__)

def transform_evaporation_timeseries_penman_to_makkink(evaporation_timeseries):
    """Return the adjusted evaporation timeserie.

    Parameters:
    * evaporation_timeseries -- timeserie with evaporation [mm/day]

    """
    result = SparseTimeseriesStub()
    month_factor = [0.400, 0.933, 1.267, 1.300, 1.300, 1.310, 1.267, 1.193, 1.170, 0.900, 0.700, 0.000]

    for evaporation_event in enumerate_events(evaporation_timeseries):
        month_number = evaporation_event[0][0].month
        factor = month_factor[month_number-1]
        result.add_value(evaporation_event[0][0], evaporation_event[0][1]*factor)

    return result


def find_pumping_station_level_control(area, find_intake):
    """Find and return the PumpingStation to be used for level control.

    Parameters:
      *area*
        Area-like object to which the searched  PumpingStation should belong
      *find_intake*
        holds if and only if the searched PumpingStation should be an intake

    """
    stations = (station for station in area.pumping_stations
                if station.into == find_intake and
                   station.is_computed == True)
    return next(stations, None)


def retrieve_incoming_timeseries(area, only_input=False):
    """Return the dictionary of intake to measured time series.

    Parameter:
      *area*
        Area to which the intakes belong
      *only_input*
        If only_input holds, this method only returns the measured time series
        of those intakes that are not used for level control, otherwise this
        method returns the measured time series of all intakes.

    Note that the measured time series of an intake is the sum of the
    measured time series of its pump lines.

    """
    incoming_timeseries = {}
    for pumping_station in area.pumping_stations:
        if pumping_station.into:
            if only_input and pumping_station.is_computed:
                continue
            timeseries = pumping_station.retrieve_sum_timeseries(None, None)
            incoming_timeseries[pumping_station] = timeseries
    return incoming_timeseries


def retrieve_outgoing_timeseries(area, only_input=False):
    """Return the dictionary of pump to measured time series.

    Parameter:
      *area*
        Area to which the pumps belong
      *only_input*
        If only_input holds, this method only returns the measured time series
        of those pumps that are not used for level control, otherwise this
        method returns the measured time series of all pumps.

    Note that the measured time series of a pump is the sum of the measured
    time series of its pump lines.

    """
    outgoing_timeseries = {}
    for pumping_station in area.pumping_stations:
        if not pumping_station.into:
            if only_input and pumping_station.is_computed:
                continue
            timeseries = pumping_station.retrieve_sum_timeseries(None, None)
            outgoing_timeseries[pumping_station] = timeseries
    return outgoing_timeseries


class VolumesConcentrations(object):

    def __init__(self, area, incoming_flows, level_control, bucket2outcome):
        self.area = area
        self.incoming_flows = incoming_flows
        self.level_control = level_control
        self.bucket2outcome = bucket2outcome

    def get_volumes(self):
        volume_timeseries = []
        volume_timeseries.append(self.incoming_flows['precipitation'])
        volume_timeseries.append(self.incoming_flows['seepage'])
        for intake in self.incoming_flows['defined_input'].keys():
            if intake.is_computed:
                assert intake.into
                volume_timeseries.append(self.level_control['intake_wl_control'])
            else:
                timeseries = TimeseriesRestrictedStub(timeseries=intake.retrieve_sum_timeseries(),
                                                                  start_date=self.start_date,
                                                                  end_date=self.end_date)
                volume_timeseries.append(timeseries)
        for bucket, outcome in self.bucket2outcome.items():
            volume_timeseries.append(self.get_incoming_timeseries(self.get_restricted_timeseries(outcome.flow_off)))
            volume_timeseries.append(self.get_incoming_timeseries(self.get_restricted_timeseries(outcome.net_drainage)))
        return volume_timeseries

    def get_concentrations(self):
        chloride_concentration_levels = []
        chloride_concentration_levels.append(self.area.concentr_chloride_precipitation)
        chloride_concentration_levels.append(self.area.concentr_chloride_seepage)
        for intake in self.incoming_flows['defined_input'].keys():
            chloride_concentration_levels.append(intake.concentr_chloride)
        for bucket, outcome in self.bucket2outcome.items():
            chloride_concentration_levels.append(bucket.concentr_chloride_flow_off)
            chloride_concentration_levels.append(bucket.concentr_chloride_drainage_indraft)
        return chloride_concentration_levels

    def get_restricted_timeseries(self, timeseries):
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=self.start_date,
                                        end_date=self.end_date)

    def get_incoming_timeseries(self, timeseries):
        incoming_timeseries = SparseTimeseriesStub()
        for event in timeseries.events():
            if event[1] < 0.0:
                incoming_timeseries.add_value(event[0], -event[1])
            else:
                incoming_timeseries.add_value(event[0], 0.0)
        return incoming_timeseries


class WaterbalanceComputer2(object):
    """Compute the waterbalance-related time series.

    for the given configuration.
    """

    def __init__(self, configuration,
                 area = None,
                 settings_loader=None,
                 bucket_computer=BucketComputer(),
                 buckets_summarizer=BucketsSummarizer(),
                 level_control_computer=LevelControlComputer(),
                 level_control_assignment=LevelControlAssignment(),
                 vertical_timeseries_computer=VerticalTimeseriesComputer(),
                 concentration_computer=ConcentrationComputer2(),
                 fraction_computer=FractionComputer(),
                 sluice_error_computer=SluiceErrorComputer(),
                 load_computer = LoadComputer()):
        """Set (among others) the function to store a time series.

        Parameter (among others):
        *area*
            WaterbalanceArea for which to compute the time series


        * bucket_computer -- computer for the bucket time series
        * level_control_computer -- computer for the level control
        * store_timeserie -- function to store a time series

        The store_timeserie argument should be a callable that stores a given
        SparseTimeseriesStub as the volume attribute of a WaterbalanceTimeserie.

        """

        self.configuration = configuration
        self.area = area

        self.settings_loader=settings_loader,

        #all computation units
        self.bucket_computer = bucket_computer
        self.buckets_summarizer = buckets_summarizer
        self.level_control_computer = level_control_computer
        self.vertical_timeseries_computer = vertical_timeseries_computer
        self.level_control_assignment = level_control_assignment
        self.concentration_computer = concentration_computer
        self.fraction_computer = fraction_computer
        self.sluice_error_computer = sluice_error_computer
        self.load_computer = load_computer

    @memoize
    def get_input_timeseries(self, start_date, end_date):
        """return (and collect) all input timeseries
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all input timeseries.
            - precipitation
            - evaporation
            - seepage
            - open_water minimum_level/maximum_level
            - incoming_timeseries[intake]
        """
        logger.debug("WaterbalanceComputer2::get_input_timeseries")

        input_ts = {}
        input_ts['precipitation'] = SparseTimeseriesStub()
        for event in self.area.retrieve_precipitation(start_date, end_date).events():
            input_ts['precipitation'].add_value(event[0], event[1])
        input_ts['evaporation'] = SparseTimeseriesStub()
        for event in self.area.retrieve_evaporation(start_date, end_date).events():
            input_ts['evaporation'].add_value(event[0], event[1])
        input_ts['seepage'] = SparseTimeseriesStub()
        for event in self.area.retrieve_seepage(start_date, end_date).events():
            input_ts['seepage'].add_value(event[0], event[1])
        input_ts['infiltration'] = SparseTimeseriesStub()
        for event in self.area.retrieve_infiltration(start_date, end_date).events():
            input_ts['infiltration'].add_value(event[0], event[1])

        input_ts['open_water'] = {}
        input_ts['open_water']['minimum_level'] = self.area.retrieve_minimum_level(start_date, end_date)
        input_ts['open_water']['maximum_level'] = self.area.retrieve_maximum_level(start_date, end_date)

        input_ts['open_water']['seepage'] = input_ts['seepage']

        for bucket in self.area.buckets:
            input_ts[bucket] = {}
            input_ts[bucket]['seepage'] = bucket.retrieve_seepage(start_date, end_date)

        input_ts['incoming_timeseries'] = {}
        for intake, timeseries in retrieve_incoming_timeseries(self.area, only_input=False).iteritems():
            sparse_timeseries = SparseTimeseriesStub()
            for event in timeseries.events():
                sparse_timeseries.add_value(event[0], event[1])
            input_ts['incoming_timeseries'][intake] = TimeseriesRestrictedStub(timeseries=sparse_timeseries,
                                                            start_date=start_date,
                                                            end_date=end_date)

        input_ts['outgoing_timeseries'] = {}
        for pump, timeseries in retrieve_outgoing_timeseries(self.area, only_input=False).iteritems():
            input_ts['outgoing_timeseries'][pump] = TimeseriesRestrictedStub(timeseries=timeseries,
                                                            start_date=start_date,
                                                            end_date=end_date)

        return input_ts

    @memoize
    def get_buckets_timeseries(self, start_date, end_date):
        """return all outcome timeseries of all buckets
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all calculated bucket timeseries. Key=bucket.
        """
        logger.debug("WaterbalanceComputer2::get_buckets_timeseries")

        input = self.get_input_timeseries(start_date, end_date)

        buckets_outcome = {}
        for bucket in self.area.buckets:
            buckets_outcome[bucket] = self.bucket_computer.compute(
                bucket,
                input['precipitation'],
                input['evaporation'],
                bucket.retrieve_seepage(start_date, end_date),
                bucket.retrieve_sewer(start_date, end_date))

        # for bucket in self.configuration.retrieve_sobek_buckets():
        #     buckets_outcome[bucket]  = bucket.get_outcome(start_date, end_date)

        return buckets_outcome

    @memoize
    def get_bucketflow_summary(self, start_date, end_date):
        """summarize outcome buckets into labels
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with summarized timeseries.

        At this moment there are some fixed labels with related to fixed flows of the bucket_flows
        Has to change in the future

        """
        logger.debug("WaterbalanceComputer2::get_bucketflow_summary")
        outcome = self.get_buckets_timeseries(start_date, end_date)
        return self.buckets_summarizer.compute(outcome, start_date, end_date)

    @memoize
    def get_vertical_open_water_timeseries(self, start_date, end_date):
        """return all timeseries directly related to openwater (vertical = rainfall, evaporation and seepage)
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all flows directly related to open water
          - rainfall
          - evaporation
          - seepage
        """
        logger.debug("WaterbalanceComputer2::get_vertical_open_water_timeseries")
        input = self.get_input_timeseries(start_date, end_date)

        # The crop evaporation factor in the next call used to be a
        # variable of the open water. Apparently the variable is a constant
        # so we just fill it in.
        crop_evaporation_factor = 1.0

        # We compute the vertical time series for a specific range of
        # dates. To do so, we set an instance method that can determine
        # whether a given date is inside that range.
        date_range = DateRange(start_date, end_date)
        self.vertical_timeseries_computer.inside_range = date_range.inside
        outcome = self.vertical_timeseries_computer.compute(self.area.surface,
                                                            crop_evaporation_factor,
                                                            input['precipitation'],
                                                            transform_evaporation_timeseries_penman_to_makkink(input['evaporation']),
                                                            input['seepage'],
                                                            input['infiltration'])

        return outcome

    @memoize
    def get_level_control_timeseries(self, start_date, end_date):
        """return all calculated flows for level_control ('peilhandhaving') and the resulting storage and level in open water
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all flows directly related to open water
          - rainfall
          - evaporation
          - seepage
            TO DO: enddate startdate storage
        """
        logger.debug("WaterbalanceComputer2::get_level_control_timeseries")
        input = self.get_input_timeseries(start_date, end_date)
        buckets_summary = self.get_bucketflow_summary(start_date, end_date)
        vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)

        # We compute the level control for a specific range of time. To do
        # so, we set an instance method that can determine whether a given
        # date is inside that range.
        date_range = DateRange(start_date, end_date)
        self.level_control_computer.inside_range = date_range.inside

        outcome = self.level_control_computer.compute(
            self.area,
            buckets_summary,
            vertical_open_water_timeseries["precipitation"],
            vertical_open_water_timeseries["evaporation"],
            vertical_open_water_timeseries["seepage"],
            vertical_open_water_timeseries["infiltration"],
            input['open_water']['minimum_level'],
            input['open_water']['maximum_level'],
            input['incoming_timeseries'],
            input['outgoing_timeseries'],
            self.area.max_intake,
            self.area.max_outtake)
        return outcome

    @memoize
    def get_level_control_pumping_stations(self):
        """Return the pair (intake, pump) pumping stations for level control.

        If the user did not define an intake for level control, this funtion
        returns None for that intake. The same holds for the pump for level
        control.

        """
        logger.debug("WaterbalanceComputer2::get_level_control_pumping_stations")
        find_intake = True
        return find_pumping_station_level_control(self.area, find_intake), \
               find_pumping_station_level_control(self.area, not find_intake)

    @memoize
    def get_open_water_incoming_flows(self, start_date, end_date):
        """ Return incoming waterflows.
        - precipitation
        - seepage
        - drained
        - flow_off
        - undrained
        - hardened
        - defined_input
        - computed_intake        """
        logger.debug("WaterbalanceComputer2::get_open_water_incoming_flows")
        input = self.get_input_timeseries(start_date, end_date)
        buckets_summary = self.get_bucketflow_summary(start_date, end_date)
        vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)
        control = self.get_level_control_timeseries(start_date, end_date)
        incoming = {}
        incoming["precipitation"] = vertical_open_water_timeseries["precipitation"]
        incoming["seepage"] = vertical_open_water_timeseries["seepage"]
        incoming["drained"] = buckets_summary.drained
        incoming["flow_off"] = buckets_summary.flow_off
        incoming["undrained"] = buckets_summary.undrained
        incoming["hardened"] = buckets_summary.hardened
        incoming["sewer"] = buckets_summary.sewer
        incoming["defined_input"]= input['incoming_timeseries']
        intake, outtake = self.get_level_control_pumping_stations()
        incoming["intake_wl_control"] = {intake: control['intake_wl_control']}
        return incoming

    @memoize
    def get_open_water_outgoing_flows(self, start_date, end_date):
        """ Return outgoing waterflows
        - evaporation
        - infiltration
        - indraft
        - defined_output
        - computed_pumps
        """
        logger.debug("WaterbalanceComputer2::get_open_water_outgoing_flows")

        input = self.get_input_timeseries(start_date, end_date)
        buckets_summary = self.get_bucketflow_summary(start_date, end_date)
        vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)
        control = self.get_level_control_timeseries(start_date, end_date)
        outgoing = {}
        outgoing["evaporation"] = vertical_open_water_timeseries["evaporation"]
        outgoing["infiltration"] = vertical_open_water_timeseries["infiltration"]
        outgoing["indraft"] = buckets_summary.indraft
        outgoing["defined_output"]= input['outgoing_timeseries']
        intake, outtake = self.get_level_control_pumping_stations()
        outgoing["outtake_wl_control"] = {outtake: control['outtake_wl_control']}
        return outgoing

    @memoize
    def get_reference_timeseries(self, start_date, end_date):
        """return (and collect) all timeseries, used for reference (measured flows at structures, waterlevel and concentrations)
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with reference timeseries

        """
        logger.debug("WaterbalanceComputer2::get_reference_timeseries")
        intakes = {}
        outtakes = {}
        for pumping_station in self.area.pumping_stations:
            if pumping_station.is_computed:
                if pumping_station.into:
                    intakes[pumping_station] = pumping_station.retrieve_sum_timeseries(None, None)
                else:
                    outtakes[pumping_station] =  pumping_station.retrieve_sum_timeseries(None, None)
        return intakes, outtakes

    @memoize
    def get_waterlevel_with_sluice_error(self, start_date, end_date):
        """ """
        logger.debug("WaterbalanceComputer2::get_waterlevel_with_sluice_error")
        calc_waterlevel = self.get_level_control_timeseries(start_date, end_date)['water_level']
        sluice_error = self.calc_sluice_error_timeseries(start_date, end_date)
        return calc_waterlevel, sluice_error

    @memoize
    def get_concentration_timeseries(self, start_date, end_date):
        logger.debug("WaterbalanceComputer2::get_concentration_timeseries")
        inflow = self.get_open_water_incoming_flows(start_date, end_date)
        level_control = self.get_level_control_timeseries(start_date, end_date)
        bucket2outcome = self.get_buckets_timeseries(start_date, end_date)

        vc = VolumesConcentrations(self.area, inflow, level_control, bucket2outcome)
        vc.start_date = start_date
        vc.end_date = end_date

        totals = TotalVolumeChlorideTimeseries(vc.get_volumes(), vc.get_concentrations())

        computer = ConcentrationComputer()
        computer.initial_concentration = self.area.init_concentration
        computer.initial_volume = self.area.init_volume
        computer.incoming_volumes, computer.incoming_chlorides = totals.compute()

        computer.outgoing_volumes = level_control['total_outgoing']
        computer.outgoing_volumes_no_chloride = \
            self.get_vertical_open_water_timeseries(start_date, end_date)['evaporation']

        return computer.compute()

    @memoize
    def get_load_timeseries(self,
            start_date, end_date, substance_string='phosphate'):

        logger.debug("WaterbalanceComputer2::get_load_timeseries")

        logger.debug("Calculating load (%s - %s)..." % (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')))

        flows = self.get_open_water_incoming_flows(start_date, end_date)
        for intake in flows['defined_input'].keys():
            if intake.is_computed:
                flows['defined_input'].pop(intake)
        # flows['defined_input'] is a dictionary from intake to time
        # series, where each intake is an intake that is not used for level
        # control
        concentrations = {}
        concentrations_incremental = {}

        nutricalc_min = self.area.retrieve_nutricalc_min(start_date,
                                                         end_date)
        nutricalc_incr = self.area.retrieve_nutricalc_min(start_date,
                                                          end_date)

        load = self.load_computer.compute(self.area, 'min', substance_string,
            flows, concentrations, start_date, end_date, nutricalc_min)
        load_incremental = self.load_computer.compute(self.area, 'incr',
            substance_string, flows, concentrations_incremental, start_date,
            end_date, nutricalc_incr)

        bucket_loads = self._compute_bucket_loads(start_date, end_date, substance_string)
        load = load + bucket_loads[0]
        load_incremental = load_incremental + bucket_loads[1]

        return load, load_incremental

    def _compute_bucket_loads(self, start_date, end_date, substance_string):

        bucket2outcome = self.get_buckets_timeseries(start_date, end_date)

        summed_loads = SummedLoadsFromBuckets(start_date, end_date, bucket2outcome)
        summed_loads.interesting_labels = ['hardened', 'drained', 'undrained', \
            'flow_off', 'sewer']
        summed_loads.summary_load = SummaryLoad(BucketsSummarizer())
        summed_loads.summary_load.start_date = start_date
        summed_loads.summary_load.end_date = end_date

        return summed_loads.compute(substance_string)

    @memoize
    def get_impact_timeseries(self,
            start_date, end_date, substance_string='phosphate'):
        logger.debug("WaterbalanceComputer2::get_impact_timeseries")

        logger.debug("Calculating impact (%s - %s)..." % (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')))

        # Concentration is specified in [mg/l] whereas discharge is specified
        # in [m3/day]. The impact is specified in [mg/m2/day]. To compute the
        # impact we follow the following procedure:
        #
        #   First we multiply the concentration by 1000 to specify the
        #   concentration in [mg/m3]. Then we multiply that value by the
        #   discharge to get to a value specified in [mg/day]. Finally we
        #   divide that value by the surface of the open water to get to a
        #   value specified in [mg/day/m2] or [mg/m2/day], otherwise known as
        #   the impact.
        loads, loads_incremental = self.get_load_timeseries(start_date, \
            end_date, substance_string)

        factor = 1000.0 / float(self.area.surface)

        for load in loads:
            load.multiply_timeseries(factor)

        for load in loads_incremental:
            load.multiply_timeseries(factor)

        return loads, loads_incremental

    @memoize
    def calc_sluice_error_timeseries(
        self, start_date, end_date):
        """return sluice error (sluitfout) as SparseTimeseriesStub

        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with reference timeseries
        TODO:          When given range 1900-2015, it only returns values for 1996-2011        """
        logger.debug("WaterbalanceComputer2::calc_sluice_error_timeseries")
        control = self.get_level_control_timeseries(
            start_date, end_date)

        ref_intakes, ref_outtakes = self.get_reference_timeseries(start_date, end_date)

        sluice_error = self.sluice_error_computer.compute(
            start_date, end_date,
            [control["intake_wl_control"], control["outtake_wl_control"]],
            ref_intakes.values() + ref_outtakes.values())

        return sluice_error

    @memoize
    def get_fraction_timeseries(self, start_date, end_date):
        """return fractions in openwater
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with reference timeseries
            - fraction_water
            TO DO: enddate startdate storage
        """
        logger.debug("WaterbalanceComputer2::get_fraction_timeseries")
        input = self.get_input_timeseries(start_date, end_date)
        buckets_summary = self.get_bucketflow_summary(start_date, end_date)
        vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)
        control = self.get_level_control_timeseries(start_date, end_date)


        intakes_timeseries = {}
        for key, timeseries in input['incoming_timeseries'].items():
            intakes_timeseries[key] = TimeseriesRestrictedStub(timeseries=timeseries,
                                                   start_date=start_date,
                                                   end_date=end_date)
        intake = find_pumping_station_level_control(self.area, True)
        if intake is None:
            logger.warning("No intake for level control is present for "
                           "area %s", self.area.name)
        else:
            intakes_timeseries[intake] = control['intake_wl_control']

        fractions = self.fraction_computer.compute(self.area,
                                                   buckets_summary,
                                                   vertical_open_water_timeseries["precipitation"],
                                                   vertical_open_water_timeseries["seepage"],
                                                   control['storage'],
                                                   control['total_outgoing'],
                                                   intakes_timeseries,
                                                   start_date,
                                                   end_date)
        return fractions

    def compute(self, start_date, end_date):
        """Compute the waterbalance-related time series

        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary of Bucket to BucketOutcome,
          2. a SparseTimeseriesStub with the daily discharge for the level control,
          3. a computed WaterbalanceOutcome.
        """
        logger.debug("WaterbalanceComputer2::compute")

        #step 1. Get input timeseries
        self.get_input_timeseries(start_date, end_date)

        #step 2. Calculate buckets
        #self.get_buckets_timeseries(start_date, end_date)

        #step 3. Summarize according to labels
        self.get_bucketflow_summary(start_date, end_date)

        #step 4. Get vertical timeseries
        self.get_vertical_open_water_timeseries(start_date, end_date)

        #step 5. Get level control
        self.get_level_control_timeseries(start_date, end_date)

        #step 6. Get sluice_error
        self.get_reference_timeseries(start_date, end_date)
        self.calc_sluice_error_timeseries(start_date, end_date)

        #step 7. Get fractions
        self.get_fraction_timeseries(start_date, end_date)

        #step 8. Get fractions
        #self.get_load_timeseries(start_date, end_date)
        self.get_impact_timeseries(start_date, end_date)

        #step 9. Get fractions
        self.get_concentration_timeseries(start_date, end_date)

        return

    def _create_concentrations(self):
        concentrations = {}

        concentrations["precipitation"] = self.area.concentr_chloride_precipitation
        concentrations["seepage"] = self.area.concentr_chloride_seepage

        # for bucket in self.area.buckets:
        #     concentrations[bucket.label_flow_off] = bucket.concentr_chloride_flow_off

        for concentr in self.configuration.config_concentrations.all().select_related('Label'):
            if not concentr.label.program_name in concentrations.keys():
                concentrations[concentr.label.program_name] = concentr.cl_concentration

        return concentrations

    def write_excel_for_test(self, template_fileloc, output_fileloc, start_date, end_date):
        export_excel_small(self, template_fileloc, output_fileloc, start_date, end_date, False)