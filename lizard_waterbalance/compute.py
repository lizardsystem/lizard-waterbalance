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
import time

from lizard_waterbalance.fraction_computer import FractionComputer
from lizard_waterbalance.level_control_computer import DateRange
from lizard_waterbalance.level_control_computer import LevelControlComputer
from lizard_waterbalance.level_control_assignment import LevelControlAssignment
from lizard_waterbalance.sluice_error_computer import SluiceErrorComputer
from lizard_waterbalance.vertical_timeseries_computer import VerticalTimeseriesComputer
from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import SparseTimeseriesStub
from timeseries.timeseriesstub import TimeseriesRestrictedStub
from timeseries.timeseriesstub import multiply_timeseries
from django.core.cache import cache

from lizard_waterbalance.bucket_computer import BucketComputer
from lizard_waterbalance.bucket_summarizer import BucketsSummarizer
from lizard_waterbalance.concentration_computer import ConcentrationComputer2
from lizard_waterbalance.load_computer import LoadComputer

from lizard_waterbalance.models import Parameter
from lizard_waterbalance.models import WaterbalanceTimeserie

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



class WaterbalanceComputer2:
    """Compute the waterbalance-related time series.

    for the given configuration.
    """

    def __init__(self, configuration,
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

        self.input = {}
        self.outcome = {}

        self.input_info = {}
        self.outcome_info = {}

        self.references = False

        self.updated = False

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
            - precipitation
            - evaporation
            - seepage
            - open_water minimum_level/maximum_level
            - incoming_timeseries[intake]
        """
        if (self.input.has_key('timeseries') and
            self.input_info['timeseries']['start_date']==start_date and
            self.input_info['timeseries']['end_date']>=end_date):
            return self.input['timeseries']
        else:
            logger.debug("get input timeseries (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            input_ts = {}
            input_ts['precipitation'] = SparseTimeseriesStub()
            for event in self.configuration.retrieve_precipitation(start_date, end_date).events():
                input_ts['precipitation'].add_value(event[0], event[1])
            input_ts['evaporation'] = SparseTimeseriesStub()
            for event in self.configuration.retrieve_evaporation(start_date, end_date).events():
                input_ts['evaporation'].add_value(event[0], event[1])
            input_ts['seepage'] = SparseTimeseriesStub()
            for event in self.configuration.retrieve_seepage(start_date, end_date).events(): #for the time_being, officially part of each bucket + openwater
                input_ts['seepage'].add_value(event[0], event[1])

            input_ts['sewer'] = self.configuration.open_water.retrieve_sewer(start_date, end_date)

            input_ts['open_water'] = {}
            input_ts['open_water']['minimum_level'] = self.configuration.open_water.retrieve_minimum_level(start_date, end_date)
            input_ts['open_water']['maximum_level'] = self.configuration.open_water.retrieve_maximum_level(start_date, end_date)

            input_ts['open_water']['seepage'] = input_ts['seepage']

            for bucket in self.configuration.retrieve_buckets():
                input_ts[bucket] = {}
                input_ts[bucket]['seepage'] = bucket.retrieve_seepage(start_date, end_date)

            input_ts['incoming_timeseries'] = {}
            for intake, timeseries in self.configuration.open_water.retrieve_incoming_timeseries(only_input=True).iteritems():
                sparse_timeseries = SparseTimeseriesStub()
                for event in timeseries.events():
                    sparse_timeseries.add_value(event[0], event[1])
                input_ts['incoming_timeseries'][intake] = TimeseriesRestrictedStub(timeseries=sparse_timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date)

            input_ts['outgoing_timeseries'] = {}
            for pump, timeseries in self.configuration.open_water.retrieve_outgoing_timeseries(only_input=True).iteritems():
                input_ts['outgoing_timeseries'][intake] = TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date)

            #store for later use (some kind of cache)
            self.input['timeseries'] = input_ts
            self.input_info['timeseries'] = {}
            self.input_info['timeseries']['start_date'] = start_date
            self.input_info['timeseries']['end_date'] = end_date

            self.updated = True

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
          1. a dictionary with all calculated bucket timeseries. Key=bucket.
        """
        if (self.outcome.has_key('buckets') and
            self.outcome_info['buckets']['start_date']==start_date and
            self.outcome_info['buckets']['end_date']>=end_date):
            return self.outcome['buckets']
        else:
            logger.debug("Calculating buckets (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            input = self.get_input_timeseries(start_date, end_date)

            buckets = self.configuration.retrieve_buckets()
            buckets_outcome = {}
            for bucket in buckets:
                buckets_outcome[bucket] = self.bucket_computer.compute(
                                                                       bucket,
                                                                       input['precipitation'],
                                                                       input['evaporation'],
                                                                       bucket.retrieve_seepage(start_date, end_date),
                                                                       input['sewer'])
            #store for later use (some kind of cache)
            #self.outcome['buckets'] = buckets_outcome
            #self.outcome_info['buckets'] = {}
            #self.outcome_info['buckets']['start_date'] = start_date
            #self.outcome_info['buckets']['end_date'] = end_date

            #self.updated = True

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

        if (self.outcome.has_key('buckets_summary') and
            self.outcome_info['buckets_summary']['start_date']==start_date and
            self.outcome_info['buckets_summary']['end_date']>=end_date):
            return self.outcome['buckets_summary']
        else:
            logger.debug("Calculating bucket_summary (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            buckets_outcome = self.get_buckets_timeseries(start_date, end_date)

            buckets_summary = self.buckets_summarizer.compute(buckets_outcome, start_date, end_date)

            #store for later use (some kind of cache)
            self.outcome['buckets_summary'] = buckets_summary
            self.outcome_info['buckets_summary'] = {}
            self.outcome_info['buckets_summary']['start_date'] = start_date
            self.outcome_info['buckets_summary']['end_date'] = end_date

            self.updated = True

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
          1. a dictionary with all flows directly related to open water
          - rainfall
          - evaporation
          - seepage
        """
        if (self.outcome.has_key('vertical_open_water') and
            self.outcome_info['vertical_open_water']['start_date']==start_date and
            self.outcome_info['vertical_open_water']['end_date']>=end_date):
            return self.outcome['vertical_open_water']
        else:
            logger.debug("Calculating vertical open water flows (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))
            input = self.get_input_timeseries(start_date, end_date)

            # The crop evaporation factor in the next call used to be a
            # variable of the open water. Apparently the variable is a constant
            # so we just fill it in.
            crop_evaporation_factor = 1.0
            date_range = DateRange(start_date, end_date)
            self.vertical_timeseries_computer.inside_range = date_range.inside
            outcome = self.vertical_timeseries_computer.compute(self.configuration.open_water.surface,
                                                                crop_evaporation_factor,
                                                                input['precipitation'],
                                                                transform_evaporation_timeseries_penman_to_makkink(input['evaporation']),
                                                                input['seepage'])
            #store for later use (some kind of cache)
            self.outcome['vertical_open_water'] = outcome
            self.outcome_info['vertical_open_water'] = {}
            self.outcome_info['vertical_open_water']['start_date'] = start_date
            self.outcome_info['vertical_open_water']['end_date'] = end_date

            self.updated = True

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
          1. a dictionary with all flows directly related to open water
          - rainfall
          - evaporation
          - seepage
            TO DO: enddate startdate storage
        """

        if (self.outcome.has_key('level_control') and
            self.outcome_info['level_control']['start_date']==start_date and
            self.outcome_info['level_control']['end_date']>=end_date):
            return self.outcome['level_control']
        else:
            logger.debug("Calculating level control (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            input = self.get_input_timeseries(start_date, end_date)
            buckets_summary = self.get_bucketflow_summary(start_date, end_date)
            vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)

            #to do: label timeseries
            date_range = DateRange(start_date, end_date)
            self.level_control_computer.inside_range = date_range.inside
            outcome = self.level_control_computer.compute(
                self.configuration.open_water,
                buckets_summary,
                vertical_open_water_timeseries["precipitation"],
                vertical_open_water_timeseries["evaporation"],
                vertical_open_water_timeseries["seepage"],
                vertical_open_water_timeseries["infiltration"],
                input['open_water']['minimum_level'],
                input['open_water']['maximum_level'],
                input['incoming_timeseries'],
                input['outgoing_timeseries'],
                start_date,
                end_date)

            #cache
            self.outcome['level_control'] = outcome

            self.outcome_info['level_control'] = {}
            self.outcome_info['level_control']['start_date'] = start_date
            self.outcome_info['level_control']['end_date'] = end_date

            self.updated = True
            return outcome

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
        incoming["defined_input"]= input['incoming_timeseries']
        incoming["intake_wl_control"] = control['intake_wl_control']
        return incoming

    def get_open_water_outgoing_flows(self, start_date, end_date):
        """ Return outgoing waterflows
        - evaporation
        - infiltration
        - indraft
        - defined_output
        - computed_pumps
        """

        input = self.get_input_timeseries(start_date, end_date)
        buckets_summary = self.get_bucketflow_summary(start_date, end_date)
        vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)
        control = self.get_level_control_timeseries(start_date, end_date)
        outgoing = {}
        outgoing["evaporation"] = vertical_open_water_timeseries["evaporation"]
        outgoing["infiltration"] = vertical_open_water_timeseries["infiltration"]
        outgoing["indraft"] = buckets_summary.indraft
        outgoing["defined_output"]= input['outgoing_timeseries']
        outgoing["outtake_wl_control"] = control["outtake_wl_control"]

        return outgoing



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
        if (self.references and
            self.reference_info['start_date']==start_date and
            self.reference_info['end_date']>=end_date):
            return self.references
        else:
            logger.debug("get structure reference timeseries (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))
            intakes = {}
            outtakes = {}
            intakes_timeseries = []
            for pumping_station in self.configuration.open_water.pumping_stations.filter(computed_level_control = True):
                if pumping_station.into:
                    intakes[pumping_station] = pumping_station.retrieve_sum_timeseries()
                else:
                    outtakes[pumping_station] =  pumping_station.retrieve_sum_timeseries()

            self.references = (intakes, outtakes)
            self.reference_info = {'start_date': start_date,
                                   'end_date': end_date}
            self.updated = True

        return intakes, outtakes

    def get_waterlevel_with_sluice_error(self, start_date, end_date,
                                         reset_period, reset_timeseries = None):
        """ """

        calc_waterlevel = self.get_level_control_timeseries(start_date, end_date)['water_level']

        sluice_error = self.calc_sluice_error_timeseries(start_date, end_date)[0]

        if not reset_timeseries:
            reset_timeseries = calc_waterlevel

        sluice_error_waterlevel = SparseTimeseriesStub()

        # We have computed the sluice error in [m3/day], however we
        # will display it as a difference in water level, so
        # [m/day]. We make that translation here.
        surface = self.configuration.open_water.surface
        previous_year = None
        for events in enumerate_events(calc_waterlevel, sluice_error, reset_timeseries):
            date = events[0][0]
            if previous_year is None or previous_year < date.year:
                waterlevel = events[2][1]
                cum_sluice_error = 0
                previous_year = date.year
            cum_sluice_error += events[1][1]
            waterlevel = events[0][1] - cum_sluice_error / surface
            sluice_error_waterlevel.add_value(date, waterlevel)
        return sluice_error_waterlevel


    def get_concentration_timeseries(self,
            start_date, end_date):
        """ Alleen chloride op dit moment"""
        if (self.outcome.has_key('concentration') and
            self.outcome_info['concentration']['start_date']==start_date and
            self.outcome_info['concentration']['end_date']>=end_date):
            return self.outcome['concentration']
        else:
            logger.debug("Calculating concentration (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))
            inflow = self.get_open_water_incoming_flows(start_date, end_date)
            outflow = self.get_open_water_outgoing_flows(start_date, end_date)
            storage = self.get_level_control_timeseries(start_date, end_date)['storage']
            concentrations = {}
            for concentr in self.configuration.config_concentrations.all().select_related('Label'):
                concentrations[concentr.label.program_name] = concentr.cl_concentration

            concentration = self.concentration_computer.compute(inflow, outflow, storage, concentrations,
                                                   start_date, end_date)

            self.outcome['concentration'] = concentration
            self.outcome_info['concentration'] = {'start_date': start_date,
                                   'end_date': end_date}
            self.updated = True

        return concentration

    def get_load_timeseries(self,
            start_date, end_date):
        """ Alleen fosfaat op dit moment"""

        # Concentration is specified in [mg/l] whereas discharge is
        # specified in [m3/day]. The impact is specified in [mg/m2/day] so
        # we first multiply the concentration by 1000 to specify it in
        # [mg/m3] and then divide the result by the surface of the open
        # water to specify it in [mg/m2/m3].
        if (self.outcome.has_key('loads') and
            self.outcome_info['loads']['start_date']==start_date and
            self.outcome_info['loads']['end_date']>=end_date):
            return self.outcome['loads']
        else:
            logger.debug("Calculating load (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            flows = self.get_open_water_incoming_flows(start_date, end_date)
            concentrations = {}
            concentrations_incremetal = {}
            for concentr in self.configuration.config_concentrations.all().select_related('Label'):
                concentrations[concentr.label.program_name] = concentr.stof_lower_concentration
                concentrations_incremetal[concentr.label.program_name] = concentr.stof_increment

            load = {}
            load_incremental = {}

            if self.configuration.open_water.nutricalc_min:
                nutricalc_min = TimeseriesRestrictedStub(timeseries=self.configuration.open_water.nutricalc_min.get_timeseries(),
                                                         start_date=start_date,
                                                         end_date=end_date)
            else:
                nutricalc_min = None

            if self.configuration.open_water.nutricalc_incr:
                nutricalc_incr = TimeseriesRestrictedStub(timeseries=self.configuration.open_water.nutricalc_incr.get_timeseries(),
                                                         start_date=start_date,
                                                         end_date=end_date)

            else:
                nutricalc_incr = None


            load = self.load_computer.compute(flows, concentrations, start_date,
                                              end_date, nutricalc_min)
            load_incremental = self.load_computer.compute(flows, concentrations_incremetal, start_date, end_date,
                                                          nutricalc_incr)

            #self.outcome['loads'] = (load, load_incremental)
            #self.outcome_info['loads'] = {'start_date': start_date,
            #                       'end_date': end_date}
            #self.updated = True

        return load, load_incremental

    def get_impact_timeseries(self,
            start_date, end_date):
        """ Alleen fosfaat op dit moment"""


        if (self.outcome.has_key('impact') and
            self.outcome_info['impact']['start_date']==start_date and
            self.outcome_info['impact']['end_date']>=end_date):
            return self.outcome['impact']
        else:
            logger.debug("Calculating impact (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            load, load_incremental = self.get_load_timeseries(start_date, end_date)

            impact = {}
            impact_incremental = {}

            factor = 1000.0 / float(self.configuration.open_water.surface)

            for key, timeserie in load.items():
                impact_timeseries = multiply_timeseries(timeserie, factor)
                impact[key] = impact_timeseries

            for key, timeserie in load_incremental.items():
                impact_timeseries = multiply_timeseries(timeserie, factor)
                impact_incremental[key] = impact_timeseries

            #store for later use (some kind of cache)
            self.outcome['impact'] = (impact, impact_incremental)
            self.outcome_info['impact'] = {}
            self.outcome_info['impact']['start_date'] = start_date
            self.outcome_info['impact']['end_date'] = end_date

            self.updated = True

        return impact, impact_incremental

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

        if (self.outcome.has_key('sluice_error') and
            self.outcome_info['sluice_error']['start_date']==start_date and
            self.outcome_info['sluice_error']['end_date']>=end_date):
            return self.outcome['sluice_error']
        else:
            logger.debug("Calculating sluice error (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            control = self.get_level_control_timeseries(
                start_date, end_date)

            ref_intakes, ref_outtakes = self.get_reference_timeseries(start_date, end_date)

            sluice_error, total_outtakes = self.sluice_error_computer.compute(
                self.configuration.open_water,
                control["intake_wl_control"],
                control["outtake_wl_control"],
                ref_intakes,
                ref_outtakes,
                start_date, end_date)


            self.outcome['sluice_error'] = (sluice_error, total_outtakes)
            self.outcome_info['sluice_error'] = {}
            self.outcome_info['sluice_error']['start_date'] = start_date
            self.outcome_info['sluice_error']['end_date'] = end_date

            self.updated = True

        return sluice_error, total_outtakes  # SparseTimeseriesStubs



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
            start_date_calc, end_date_calc)[0]  # Is actually quite fast.
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
            timestep=timestep,
            hint_datetime_start=start_date_calc,
            hint_datetime_end=end_date_calc)
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
            - fraction_water
            TO DO: enddate startdate storage
        """
        if (self.outcome.has_key('fraction_water') and
            self.outcome_info['fraction_water']['start_date']==start_date and
            self.outcome_info['fraction_water']['end_date']>=end_date):

            return self.outcome['fraction_water']
        else:
            logger.debug("Calculating fraction (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            input = self.get_input_timeseries(start_date, end_date)
            buckets_summary = self.get_bucketflow_summary(start_date, end_date)
            vertical_open_water_timeseries = self.get_vertical_open_water_timeseries(start_date, end_date)
            control = self.get_level_control_timeseries(start_date, end_date)


            #intakes, tmp_timeseries = self.retrieve_intakes_timeseries(configuration.open_water)
            #TO DO
            intakes_timeseries = {}
            for key, timeseries in input['incoming_timeseries'].items():
                intakes_timeseries[key] = TimeseriesRestrictedStub(timeseries=timeseries,
                                                       start_date=start_date,
                                                       end_date=end_date)
            intakes_timeseries['intake_wl_control'] = control['intake_wl_control']

            fractions = self.fraction_computer.compute(self.configuration.open_water,
                                                       buckets_summary,
                                                       vertical_open_water_timeseries["precipitation"],
                                                       vertical_open_water_timeseries["seepage"],                                                       control['storage'],
                                                       control['total_outgoing'],
                                                       intakes_timeseries,
                                                       start_date,
                                                       end_date)

            self.outcome['fraction_water'] = fractions
            self.outcome_info['fraction_water'] = {}
            self.outcome_info['fraction_water']['start_date'] = start_date
            self.outcome_info['fraction_water']['end_date'] = end_date

            self.updated = True

            return fractions

    def cache_if_updated(self):
        """ save computer to cache """
        if self.updated:
            logger.debug("save waterbalance computer from cache, with code: wb_computer_%i_store"%self.configuration.id)

            t1 = time.time()
            updated = self.updated
            self.updated = False

            cache.set(u'wb_computer_%i_store'%self.configuration.id, self, 24*60*60)
            cache.set(u'wb_computer_%i_stored_date'%self.configuration.id, time.time(), 24*60*60)

            self.updated = updated

            logger.debug("Saved updated watercomputer to cache in %s seconds", time.time() - t1)



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
