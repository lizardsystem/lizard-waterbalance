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
#
# Initial programmer: Pieter Swinkels
# Initial date:       2010-11-26
#
#******************************************************************************

import datetime
import logging

from lizard_waterbalance.fraction_computer import FractionComputer
from lizard_waterbalance.level_control_computer import LevelControlComputer
from lizard_waterbalance.level_control_storage import LevelControlAssignment
from lizard_waterbalance.level_control_storage import LevelControlStorage
from lizard_waterbalance.sluice_error_computer import SluiceErrorComputer
from lizard_waterbalance.store import store_waterbalance_timeserie
from lizard_waterbalance.vertical_timeseries_computer import VerticalTimeseriesComputer
from lizard_waterbalance.vertical_timeseries_storage import VerticalTimeseriesStorage
from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import TimeseriesStub
from timeseries.timeseriesstub import TimeseriesRestrictedStub

from lizard_waterbalance.bucket_computer import BucketsComputer
from lizard_waterbalance.bucket_summarizer import BucketsSummarizer
from lizard_waterbalance.concentration_computer import ConcentrationComputer
from lizard_waterbalance.models import Parameter
from lizard_waterbalance.models import WaterbalanceTimeserie

logger = logging.getLogger(__name__)


class OpenWaterOutcome:
    """Stores the time series that are computed for an OpenWater.

    Instance variables:
    * precipitation -- time series for *neerslag*
    * evaporation -- time series for *verdamping*

    """
    def __init__(self):
        self.precipitation = TimeseriesStub()
        self.evaporation = TimeseriesStub()
        self.seepage = TimeseriesStub()

    def name2timeseries(self):
        return {"precipitation": self.precipitation,
                "evaporation": self.evaporation,
                "seepage": self.seepage}


def transform_evaporation_timeseries_penman_to_makkink(evaporation_timeseries):
    """Return the adjusted evaporation timeserie.

    Parameters:
    * evaporation_timeseries -- timeserie with evaporation [mm/day]

    """
    result = TimeseriesStub()
    month_factor = [0.400, 0.933, 1.267, 1.300, 1.300, 1.310, 1.267, 1.193, 1.170, 0.900, 0.700, 0.000]


    for evaporation_event in enumerate_events(evaporation_timeseries):
        month_number = evaporation_event[0][0].month
        factor = month_factor[month_number-1]
        result.add_value(evaporation_event[0][0], evaporation_event[0][1]*factor)

    return result


class WaterbalanceOutcome:
    """Contains the computed time series that are part of a waterbalance.

    Instance variables:
    * open_water_timeseries -- dictionary that contains the summed discharges of the buckets to and from the open water
    * open_water_fractions -- dictionary that contains the fractions of the discharges of the buckets to and from the open water
    * level_control_assignment -- dictionary that contains the level control time series
    * intake_fractions -- dictionary that contains the fractions of all the intakes and pumps

    """

    def __init__(self):

        self.open_water_timeseries = {}
        self.level_control_assignment = {}
        self.open_water_fractions = {}
        self.intake_fractions = {}

class WaterbalanceComputer2:
    """Compute the waterbalance-related time series.

    for the given configuration.
    """

    def __init__(self, configuration,
                 settings_loader=None,
                 buckets_computer=BucketsComputer(),
                 buckets_summarizer=BucketsSummarizer(),
                 level_control_computer=LevelControlComputer(),
                 level_control_assignment=LevelControlAssignment(),
                 vertical_timeseries_computer=VerticalTimeseriesComputer(),
                 concentration_computer=ConcentrationComputer(),
                 fraction_computer=FractionComputer(),
                 sluice_error_computer=SluiceErrorComputer()):
        """Set (among others) the function to store a time series.

        Parameter (among others):
        *area*
            WaterbalanceArea for which to compute the time series


        * buckets_computer -- computer for the bucket time series
        * level_control_computer -- computer for the level control
        * store_timeserie -- function to store a time series

        The store_timeserie argument should be a callable that stores a given
        TimeseriesStub as the volume attribute of a WaterbalanceTimeserie.

        """

        self.configuration = configuration

        self.settings_loader=settings_loader,

        #all computation units
        self.buckets_computer = buckets_computer
        self.buckets_summarizer = buckets_summarizer
        self.level_control_computer = level_control_computer
        self.vertical_timeseries_computer = vertical_timeseries_computer
        self.level_control_assignment = level_control_assignment
        self.concentration_computer = concentration_computer
        self.fraction_computer = fraction_computer
        self.sluice_error_computer = sluice_error_computer

        self.input = {}
        self.outcome = {}

        self.input_info = {}
        self.outcome_info = {}

        #kan deze niet weg of pas opgegeven bij samenvatten of opslaan?
        # self.buckets_summarizer = BucketsSummarizer()
        #self.vertical_timeseries_storage = VerticalTimeseriesStorage(store_timeserie=self.store_timeserie)
        #self.store_timeserie = store_timeserie
        #self.level_control_storage = LevelControlStorage(store_timeserie=self.store_timeserie)

    #TO DO
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

        """
        if (self.input.has_key('timeseries') and self.input_info['timeseries']['start_date']==start_date and self.input_info['timeseries']['end_date']==end_date):
            input_ts = self.input['timeseries']
        else:
            input_ts = {}
            input_ts['precipitation'] = self.configuration.retrieve_precipitation(start_date, end_date)
            input_ts['evaporation'] = self.configuration.retrieve_evaporation(start_date, end_date)
            input_ts['seepage'] = self.configuration.retrieve_seepage(start_date, end_date) #for the time_being, officially part of each bucket + openwater

            input_ts['open_water'] = {}
            input_ts['open_water']['minimum_level'] = TimeseriesRestrictedStub(timeseries=self.configuration.open_water.retrieve_minimum_level(),
                                                            start_date=start_date,
                                                            end_date=end_date)
            input_ts['open_water']['maximum_level'] = TimeseriesRestrictedStub(timeseries=self.configuration.open_water.retrieve_maximum_level(),
                                                            start_date=start_date,
                                                            end_date=end_date)
            input_ts['open_water']['seepage'] = input_ts['seepage'] #temp solution

            for bucket in self.configuration.retrieve_buckets():
                input_ts[bucket.slug] = {}
                input_ts[bucket.slug]['seepage'] = input_ts['seepage']# tmp solution: bucket.retrieve_seepage(start_date, end_date)

            input_ts['incoming_timeseries'] = {}
            for intake, timeseries in self.configuration.open_water.retrieve_incoming_timeseries(only_input=True).iteritems():
                slug = intake.id
                input_ts['incoming_timeseries'][slug] = TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date)

            input_ts['outgoing_timeseries'] = {}
            for pump, timeseries in self.configuration.open_water.retrieve_outgoing_timeseries(only_input=True).iteritems():
                slug = pump.id
                input_ts['outgoing_timeseries'][slug] = TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date)

            #store for later use (some kind of cache)
            self.input['timeseries'] = input_ts
            self.input_info['timeseries'] = {}
            self.input_info['timeseries']['start_date'] = start_date
            self.input_info['timeseries']['end_date'] = end_date

        return input_ts


    def get_buckets_timeseries(self, start_date, end_date):
        """return all outcome timeseries of all buckets
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all calculated bucket timeseries.

        """
        if (self.outcome.has_key('buckets') and self.outcome_info['buckets']['start_date']==start_date and self.outcome_info['buckets']['end_date']==end_date):
            buckets_outcome = self.outcome['buckets']
        else:
            input = self.get_input_timeseries(start_date, end_date)

            buckets = self.configuration.retrieve_buckets()
            buckets_outcome = self.buckets_computer.compute(buckets,
                                                            input['precipitation'],
                                                            input['evaporation'],
                                                            input['seepage']) #start_date, end_date??? + seepage for each bucket. this for the time being

            #store for later use (some kind of cache)
            self.outcome['buckets'] = buckets_outcome
            self.outcome_info['buckets'] = {}
            self.outcome_info['buckets']['start_date'] = start_date
            self.outcome_info['buckets']['end_date'] = end_date

        return buckets_outcome

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

        if (self.outcome.has_key('buckets_summary') and self.outcome_info['buckets_summary']['start_date']==start_date and self.outcome_info['buckets_summary']['end_date']==end_date):
            buckets_summary = self.outcome['buckets_summary']
        else:
            bucket_outcome = self.get_buckets_timeseries(start_date, end_date)

            buckets_summary = self.buckets_summarizer.compute(bucket_outcome)

            #outcome = {"undrained": buckets_summary.undrained,
            #          "drained": buckets_summary.drained,
            #          "hardened": buckets_summary.hardened,
            #          "flow_off": buckets_summary.flow_off,
            #          "indraft": buckets_summary.indraft,
            #          "totals":buckets_summary.totals}


            #store for later use (some kind of cache)
            self.outcome['buckets_summary'] = buckets_summary
            self.outcome_info['buckets_summary'] = {}
            self.outcome_info['buckets_summary']['start_date'] = start_date
            self.outcome_info['buckets_summary']['end_date'] = end_date

        return buckets_summary

    def get_vertical_open_water_timeseries(self, start_date, end_date):
        """return all timeseries directly related to openwater (vertical = rainfall, evaporation and seepage)
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all flows directly related to open water (rainfall, evaporation and seepage).

        """
        if (self.outcome.has_key('vertical_open_water') and self.outcome_info['vertical_open_water']['start_date']==start_date and self.outcome_info['vertical_open_water']['end_date']==end_date):
             outcome = self.outcome['vertical_open_water']
        else:
            input = self.get_input_timeseries(start_date, end_date)

            # The crop evaporation factor in the next call used to be a
            # variable of the open water. Apparently the variable is a constant
            # so we just fill it in.
            crop_evaporation_factor = 1.0
            vertical_timeseries = self.vertical_timeseries_computer.compute(self.configuration.open_water.surface,
                                                                            crop_evaporation_factor,
                                                                            input['precipitation'],
                                                                            transform_evaporation_timeseries_penman_to_makkink(input['evaporation']), #place this function to VerticalComputer()
                                                                            input['seepage'])#seepage nog general, but specific for buckets and openwater

            outcome = {"precipitation":vertical_timeseries[0],
                      "evaporation":vertical_timeseries[1],
                      "seepage":vertical_timeseries[2],
                      "infiltration":vertical_timeseries[3]}

            #store for later use (some kind of cache)
            self.outcome['vertical_open_water'] = outcome
            self.outcome_info['vertical_open_water'] = {}
            self.outcome_info['vertical_open_water']['start_date'] = start_date
            self.outcome_info['vertical_open_water']['end_date'] = end_date

        return outcome

    def get_level_control_timeseries(self, start_date, end_date):
        """return all calculated flows for level_control ('peilhandhaving') and the resulting storage and level in open water
        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with all flows directly related to open water (rainfall, evaporation and seepage).

            TO DO: enddate startdate storage
        """

        if (self.outcome.has_key('level_control') and self.outcome_info['level_control']['start_date']==start_date and self.outcome_info['level_control']['end_date']==end_date):
            return {'level_control':self.outcome['level_control'], 'open_water_cnt':self.outcome['open_water_cnt']}
        else:
            input = self.get_input_timeseries(start_date, end_date)
            buckets_summary = self.get_bucketflow_summary(start_date, end_date)
            vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)

            #to do: label timeseries
            intake_time_series, pump_time_series, storage, water_level_timeseries = self.level_control_computer.compute(
                                                                self.configuration.open_water,
                                                                buckets_summary,
                                                                vertical_open_water_timeseries.values(),
                                                                input['open_water']['minimum_level'],
                                                                input['open_water']['maximum_level'],
                                                                input['incoming_timeseries'].values(),
                                                                input['outgoing_timeseries'].values())


            #devide flow over punpingstation
            pumping_stations = self.configuration.open_water.pumping_stations.all()
            outcome = {}
            outcome['level_control'] = self.level_control_assignment.compute((intake_time_series, pump_time_series), #to do: label timeseries
                                                                             pumping_stations)

            outcome['level_control']['intake_time_series'] = intake_time_series
            outcome['level_control']['pump_time_series'] = pump_time_series

            outcome['open_water_cnt'] = {}
            outcome['open_water_cnt']['storage'] = storage
            outcome['open_water_cnt']['water level'] = water_level_timeseries

            #cache
            self.outcome['level_control'] = outcome['level_control']
            self.outcome['open_water_cnt'] = outcome['open_water_cnt']
            self.outcome_info['level_control'] = {}
            self.outcome_info['level_control']['start_date'] = start_date
            self.outcome_info['level_control']['end_date'] = end_date
            return outcome

    #to do
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



        """
        intakes = []
        intakes_timeseries = []
        for pumping_station in open_water.pumping_stations.all():
            if pumping_station.into:
                intakes.append(pumping_station)
                if pumping_station.computed_level_control:
                    if pumping_station.level_control is None:
                        timeseries = TimeseriesStub()
                    else:
                        timeseries = pumping_station.level_control.get_timeseries()
                else:
                    timeseries = pumping_station.retrieve_sum_timeseries()
                intakes_timeseries.append(timeseries)
        return intakes, intakes_timeseries
        """


    def calc_sluice_error_timeseries(
        self, start_date_calc, end_date_calc):
        """return sluice error (sluitfout) as TimeseriesStub

        Args:
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary with reference timeseries
        """
        logger.debug("Calculating sluice error (%s - %s)..." % (
                start_date_calc.strftime('%Y-%m-%d'),
                end_date_calc.strftime('%Y-%m-%d')))

        timeseries = self.get_level_control_timeseries(
            start_date_calc, end_date_calc)
        timeseries_sluice_error = [
            timeseries['level_control']['intake_time_series'],
            timeseries['level_control']['pump_time_series'],
            timeseries['open_water_cnt']['storage'],
            ]
        sluice_error = self.sluice_error_computer.compute(
            self.configuration.open_water,
            timeseries_sluice_error,
            start_date_calc, end_date_calc) #??? input van kunstwerk metingen?

        return sluice_error  # TimeseriesStub

    def calc_and_store_sluice_error_timeseries(
        self, start_date_calc, end_date_calc, timestep,
        name=None, parameter=None):
        """
        Calculate, store and return waterbalance timeseries for sluice error.
        """
        if name is None:
            name = 'sluice_error'
        if parameter is None:
            parameter, _ = Parameter.objects.get_or_create(
                name='sluitfout', unit='m')

        ts = self.calc_sluice_error_timeseries(
            start_date_calc, end_date_calc)  # Is actually quite fast.
        if timestep == WaterbalanceTimeserie.TIMESTEP_DAY:
            ts_dict = dict(ts.events())
        elif timestep == WaterbalanceTimeserie.TIMESTEP_MONTH:
            ts_dict = dict(ts.monthly_events())
        else:
            logger.error("Timestep %d is not supported yet." % timestep)
            return None
        result_timeseries = WaterbalanceTimeserie.create(
            name=name,
            parameter=parameter,
            timeseries=ts_dict,
            configuration=self.configuration,
            timestep=timestep)
        return result_timeseries

    def get_sluice_error_timeseries(
        self, start_date, end_date,
        start_date_calc=None, end_date_calc=None,
        timestep=WaterbalanceTimeserie.TIMESTEP_MONTH,
        force_recalculate=False):
        """
        Return WaterbalanceTimeserie of sluice error.

        If data not available, it will be calculated and stored.

        TODO: use dates consistently. Now also datetimes are used.
        """
        name = 'sluice_error'
        parameter, _ = Parameter.objects.get_or_create(
            name='sluitfout', unit='m')

        logger.debug(
            "Searching for WaterbalanceTimeserie (%s %s %s timestep=%s)" %
            (name, parameter, self.configuration, timestep))

        # Try to find existing waterbalance timeseries.
        wb_ts = WaterbalanceTimeserie.objects.filter(
            name=name,
            parameter=parameter,
            configuration=self.configuration,
            timestep=timestep)

        # Determine if we need (re)calculation.
        need_calculation = False
        if force_recalculate:
            logger.debug("Forced recalculation.")
            need_calculation = True
        if not need_calculation and not wb_ts:
            logger.debug("Could not find existing ts for "
                         "sluice_error, recalculating.")
            need_calculation = True
        if not need_calculation and wb_ts:
            # There should be only one
            if len(wb_ts) > 1:
                logger.error(
                    "More than one timeseries found, recalculating.")
                need_calculation = True
            if not wb_ts[0].in_daterange(start_date):
                logger.debug(
                    "Start_date %s not in available data, "
                    "recalculating." % start_date)
                need_calculation = True
            if not wb_ts[0].in_daterange(end_date):
                logger.debug(
                    "End_date %s not in available data, "
                    "recalculating." % end_date)
                need_calculation = True

        # (Re)calculate sluice error.
        if need_calculation:
            if start_date_calc is None:
                start_date_calc = datetime.datetime(1900, 1, 1)
            if end_date_calc is None:
                # Make 1 month margin because aggregation truncates.
                end_date_calc = end_date + datetime.timedelta(days=31)
            result_timeseries = self.calc_and_store_sluice_error_timeseries(
                start_date_calc, end_date_calc, timestep,
                name=name, parameter=parameter)
        else:
            result_timeseries = wb_ts[0]

        return result_timeseries


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

            TO DO: enddate startdate storage
        """
        if (self.outcome.has_key('fraction_water') and self.outcome_info['fraction_water']['start_date']==start_date and self.outcome_info['fraction_water']['end_date']==end_date):
            return self.outcome['fraction_water']
        else:
            input = self.get_input_timeseries(start_date, end_date)
            buckets_summary = self.get_bucketflow_summary(start_date, end_date)
            vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)
            control = self.get_level_control_timeseries(start_date, end_date)


            #intakes, tmp_timeseries = self.retrieve_intakes_timeseries(configuration.open_water)
            #TO DO
            intakes_timeseries = [TimeseriesRestrictedStub(timeseries=timeseries,
                                                       start_date=start_date,
                                                       end_date=end_date) for timeseries in input['incoming_timeseries'].values()]

            fractions = self.fraction_computer.compute(self.configuration.open_water,
                                                       buckets_summary,
                                                       vertical_open_water_timeseries.values(),
                                                       control['open_water_cnt']['storage'],
                                                       intakes_timeseries)

            self.outcome['fraction_water'] = fractions
            self.outcome_info['fraction_water'] = {}
            self.outcome_info['fraction_water']['start_date'] = start_date
            self.outcome_info['fraction_water']['end_date'] = end_date

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
          2. a TimeseriesStub with the daily discharge for the level control,
          3. a computed WaterbalanceOutcome.
        """

        #step 1. Get input timeseries
        input = self.get_input_timeseries(start_date, end_date)

        #step 2. Calculate buckets
        buckets = self.get_buckets_timeseries(start_date, end_date)

        #step 3. Summarize according to labels
        buckets_summary = self.get_bucketflow_summary(start_date, end_date)

        #step 4. Get vertical timeseries
        vertical_openwater = self.get_vertical_open_water_timeseries(start_date, end_date)

        #step 5. Get level control
        level_control = self.get_level_control_timeseries(start_date, end_date)

        #step 6. Get sluice_error
        reference_timeseries = self.get_reference_timeseries(start_date, end_date)
        sluice_error = self.get_sluice_error_timeseries(start_date, end_date)

        #step 7. Get fractions
        fractions = self.get_fraction_timeseries(start_date, end_date)

        #configuration.open_water.save() #???

        return input, buckets, buckets_summary, vertical_openwater, level_control, reference_timeseries, sluice_error, fractions #uitbreiden


class WaterbalanceComputer:
    """Computes the waterbalance time series for a given area."""

    def __init__(self, buckets_computer=None,
                 level_control_computer=None,
                 store_timeserie=store_waterbalance_timeserie):
        """Set (among others) the function to store a time series.

        Parameter (among others):
        * buckets_computer -- computer for the bucket time series
        * level_control_computer -- computer for the level control
        * store_timeserie -- function to store a time series

        The store_timeserie argument should be a callable that stores a given
        TimeseriesStub as the volume attribute of a WaterbalanceTimeserie.

        """
        self.store_timeserie = lambda m, n, t: None
        if buckets_computer is None:
            self.buckets_computer = BucketsComputer()
        else:
            self.buckets_computer = buckets_computer
        if level_control_computer is None:
            self.level_control_computer = LevelControlComputer()
        else:
            self.level_control_computer = level_control_computer
        self.buckets_summarizer = BucketsSummarizer()
        self.vertical_timeseries_computer = VerticalTimeseriesComputer()
        self.vertical_timeseries_storage = VerticalTimeseriesStorage(store_timeserie=self.store_timeserie)
        self.level_control_assignment = LevelControlAssignment()
        self.level_control_storage = LevelControlStorage(store_timeserie=self.store_timeserie)
        self.fraction_computer = FractionComputer()

    def compute(self, configuration, start_date, end_date):
        """Compute the waterbalance-related time series for the given configuration.

        Args:
          *configuration*
            WaterbalanceConfiguration for which to compute the time series
          *start_date*
            date of the first day for which to compute the time series
          *end_date*
            date of the day *after* the last day for which to compute the time
            series

        This method returns a tuple that contains
          1. a dictionary of Bucket to BucketOutcome,
          2. a TimeseriesStub with the daily discharge for the level control,
          3. a computed WaterbalanceOutcome.

        The WaterbalanceOutcome contains all the time series of the
        waterbalance. The first two elements of the tuple are only returned for
        debugging purposes. Especially the second element might be removed in a
        later version.

        """
        outcome = WaterbalanceOutcome()

        precipitation = configuration.retrieve_precipitation(start_date, end_date)
        evaporation = configuration.retrieve_evaporation(start_date, end_date)
        seepage = configuration.retrieve_seepage(start_date, end_date)
        buckets = configuration.retrieve_buckets()
        bucket2outcome = self.buckets_computer.compute(buckets,
                                                       precipitation,
                                                       evaporation,
                                                       seepage)

        buckets_summary = self.buckets_summarizer.compute(bucket2outcome)

        self.store_timeserie(configuration.open_water, "undrained",
                                     buckets_summary.undrained)
        self.store_timeserie(configuration.open_water, "drained",
                                     buckets_summary.drained)
        self.store_timeserie(configuration.open_water, "hardened",
                                     buckets_summary.hardened)
        self.store_timeserie(configuration.open_water, "flow_off",
                                     buckets_summary.flow_off)
        self.store_timeserie(configuration.open_water, "indraft",
                                     buckets_summary.indraft)

        outcome.open_water_timeseries = {"undrained": buckets_summary.undrained,
                                         "drained": buckets_summary.drained,
                                         "hardened": buckets_summary.hardened,
                                         "flow_off": buckets_summary.flow_off,
                                         "indraft": buckets_summary.indraft}

        # The crop evaporation factor in the next call used to be a variable of
        # the open water. Apparently the variable is a constant so we just fill
        # it in.
        crop_evaporation_factor = 1.0
        vertical_timeseries = self.vertical_timeseries_computer.compute(configuration.open_water.surface,
                                                                        crop_evaporation_factor,
                                                                        precipitation,
                                                                        transform_evaporation_timeseries_penman_to_makkink(evaporation),
                                                                        seepage)
        self.vertical_timeseries_storage.store(vertical_timeseries,
                                               configuration.open_water)

        outcome.open_water_timeseries["precipitation"] = vertical_timeseries[0]
        outcome.open_water_timeseries["evaporation"] = vertical_timeseries[1]
        outcome.open_water_timeseries["seepage"] = vertical_timeseries[2]
        outcome.open_water_timeseries["infiltration"] = vertical_timeseries[3]

        incoming_timeseries = []
        for timeseries in configuration.open_water.retrieve_incoming_timeseries(only_input=True).values():
            incoming_timeseries.append(TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date))
        outgoing_timeseries = []
        for timeseries in configuration.open_water.retrieve_outgoing_timeseries(only_input=True).values():
            outgoing_timeseries.append(TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date))

        minimum_level_timeseries = TimeseriesRestrictedStub(timeseries=configuration.open_water.retrieve_minimum_level(),
                                                            start_date=start_date,
                                                            end_date=end_date)

        maximum_level_timeseries = TimeseriesRestrictedStub(timeseries=configuration.open_water.retrieve_maximum_level(),
                                                            start_date=start_date,
                                                            end_date=end_date)

        level_control = self.level_control_computer.compute(configuration.open_water,
                                                            buckets_summary,
                                                            vertical_timeseries,
                                                            minimum_level_timeseries,
                                                            maximum_level_timeseries,
                                                            incoming_timeseries,
                                                            outgoing_timeseries)

        pumping_stations = configuration.open_water.pumping_stations.all()
        outcome.level_control_assignment = self.level_control_assignment.compute(level_control[0:2],
                                                           pumping_stations)
        self.level_control_storage.store(pumping_stations, outcome.level_control_assignment)

        outcome.open_water_timeseries["storage"] = level_control[2]
        self.store_timeserie(configuration.open_water, "storage", outcome.open_water_timeseries["storage"])

        outcome.open_water_timeseries["water level"] = level_control[3]

        sluice_error = SluiceErrorComputer().compute(configuration.open_water,
                                                     level_control[0:2],
                                                     start_date, end_date)
        outcome.open_water_timeseries["sluice error"] = sluice_error

        intakes, tmp_timeseries = self.retrieve_intakes_timeseries(configuration.open_water)
        intakes_timeseries = [TimeseriesRestrictedStub(timeseries=timeseries,
                                                       start_date=start_date,
                                                       end_date=end_date) for timeseries in tmp_timeseries]
        fractions = self.fraction_computer.compute(configuration.open_water,
                                                   buckets_summary,
                                                   vertical_timeseries,
                                                   outcome.open_water_timeseries["storage"],
                                                   intakes_timeseries)

        self.store_timeserie(configuration.open_water, "fractions_initial",
                             fractions[0])
        outcome.open_water_fractions["initial"] = fractions[0]
        self.store_timeserie(configuration.open_water, "fractions_precipitation",
                             fractions[1])
        outcome.open_water_fractions["precipitation"] = fractions[1]
        self.store_timeserie(configuration.open_water, "fractions_seepage",
                             fractions[2])
        outcome.open_water_fractions["seepage"] = fractions[2]
        self.store_timeserie(configuration.open_water, "fractions_hardened",
                             fractions[3])
        outcome.open_water_fractions["hardened"] = fractions[3]
        self.store_timeserie(configuration.open_water, "fractions_drained",
                             fractions[4])
        outcome.open_water_fractions["drained"] = fractions[4]
        self.store_timeserie(configuration.open_water, "fractions_undrained",
                             fractions[5])
        outcome.open_water_fractions["undrained"] = fractions[5]
        self.store_timeserie(configuration.open_water, "fractions_flow_off",
                             fractions[6])
        outcome.open_water_fractions["flow_off"] = fractions[6]
        for index, intake in enumerate(intakes):
            self.store_timeserie(intake, "fractions", fractions[7 + index])
            intake.save()
            outcome.intake_fractions[intake] = fractions[7 + index]

        configuration.open_water.save()

        return bucket2outcome, level_control, outcome

    def retrieve_intakes_timeseries(self, open_water):
        """Return the pair of lists of intakes and their timeseries.

        Parameter:
        * open_water -- OpenWater to which the intakes belong
        """
        intakes = []
        intakes_timeseries = []
        for pumping_station in open_water.pumping_stations.all():
            if pumping_station.into:
                intakes.append(pumping_station)
                timeseries = pumping_station.retrieve_sum_timeseries()
                intakes_timeseries.append(timeseries)
        return intakes, intakes_timeseries
