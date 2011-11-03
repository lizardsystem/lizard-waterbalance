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

import logging

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

from lizard_waterbalance.bucket_computer import BucketComputer
from lizard_waterbalance.bucket_summarizer import BucketsSummarizer
from lizard_waterbalance.concentration_computer import ConcentrationComputer2
from lizard_waterbalance.load_computer import LoadComputer

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
                   station.computed_level_control == True)
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
            if only_input and pumping_station.computed_level_control:
                continue
            timeseries = pumping_station.retrieve_sum_timeseries()
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
            if only_input and pumping_station.computed_level_control:
                continue
            timeseries = pumping_station.retrieve_sum_timeseries()
            outgoing_timeseries[pumping_station] = timeseries
    return outgoing_timeseries


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
        logger.debug("WaterbalanceComputer2::get_input_timeseries")
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
            for event in self.area.retrieve_precipitation(start_date, end_date).events():
                input_ts['precipitation'].add_value(event[0], event[1])
            input_ts['evaporation'] = SparseTimeseriesStub()
            for event in self.area.retrieve_evaporation(start_date, end_date).events():
                input_ts['evaporation'].add_value(event[0], event[1])
            input_ts['seepage'] = SparseTimeseriesStub()
            for event in self.area.retrieve_seepage(start_date, end_date).events():
                input_ts['seepage'].add_value(event[0], event[1])

            input_ts['sewer'] = self.area.retrieve_sewer(start_date, end_date)

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
        logger.debug("WaterbalanceComputer2::get_buckets_timeseries")
        if (self.outcome.has_key('buckets') and
            self.outcome_info['buckets']['start_date']==start_date and
            self.outcome_info['buckets']['end_date']>=end_date):
            return self.outcome['buckets']
        else:
            logger.debug("Calculating buckets (%s - %s)..." % (
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')))

            input = self.get_input_timeseries(start_date, end_date)

            buckets_outcome = {}
            for bucket in self.area.buckets:
                buckets_outcome[bucket] = self.bucket_computer.compute(
                                                                       bucket,
                                                                       input['precipitation'],
                                                                       input['evaporation'],
                                                                       bucket.retrieve_seepage(start_date, end_date),
                                                                       input['sewer'])


            for bucket in self.configuration.retrieve_sobek_buckets():
                buckets_outcome[bucket]  = bucket.get_outcome(start_date, end_date)

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
        logger.debug("WaterbalanceComputer2::get_bucketflow_summary")

        if (self.outcome.has_key('buckets_summary') and
            self.outcome_info['buckets_summary']['start_date']==start_date and
            self.outcome_info['buckets_summary']['end_date']>=end_date):
            pass
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

        return self.outcome['buckets_summary']

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

            # We compute the vertical time series for a specific range of
            # dates. To do so, we set an instance method that can determine
            # whether a given date is inside that range.
            date_range = DateRange(start_date, end_date)
            self.vertical_timeseries_computer.inside_range = date_range.inside
            outcome = self.vertical_timeseries_computer.compute(self.area.surface,
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
        logger.debug("WaterbalanceComputer2::get_level_control_timeseries")

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
                self.area.max_outlet)

            #cache
            self.outcome['level_control'] = outcome

            self.outcome_info['level_control'] = {}
            self.outcome_info['level_control']['start_date'] = start_date
            self.outcome_info['level_control']['end_date'] = end_date

            self.updated = True
            return outcome

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
        logger.debug("WaterbalanceComputer2::get_reference_timeseries")
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
            for pumping_station in self.area.pumping_stations.filter(computed_level_control = True):
                if pumping_station.into:
                    intakes[pumping_station] = pumping_station.retrieve_sum_timeseries()
                else:
                    outtakes[pumping_station] =  pumping_station.retrieve_sum_timeseries()

            self.references = (intakes, outtakes)
            self.reference_info = {'start_date': start_date,
                                   'end_date': end_date}
            self.updated = True

        return intakes, outtakes

    def get_waterlevel_with_sluice_error(self, start_date, end_date):
        """ """
        logger.debug("WaterbalanceComputer2::get_waterlevel_with_sluice_error")

        calc_waterlevel = self.get_level_control_timeseries(start_date, end_date)['water_level']

        sluice_error = self.calc_sluice_error_timeseries(start_date, end_date)

        return calc_waterlevel, sluice_error


    def get_concentration_timeseries(self,
            start_date, end_date):
        """ Alleen chloride op dit moment"""
        logger.debug("WaterbalanceComputer2::get_concentration_timeseries")
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

            concentrations = self._create_concentrations()
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
        logger.debug("WaterbalanceComputer2::get_load_timeseries")

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
            # flows['defined_input'] is a dictionary from intake to time
            # series, where each intake is an intake that is not used for level
            # control
            concentrations = {}
            concentrations_incremetal = {}
            for concentr in self.configuration.config_concentrations.all().select_related('Label'):
                concentrations[concentr.label.program_name] = concentr.stof_lower_concentration
                concentrations_incremetal[concentr.label.program_name] = concentr.stof_increment

            nutricalc_min = self.area.retrieve_nutricalc_min(start_date,
                                                             end_date)
            nutricalc_incr = self.area.retrieve_nutricalc_min(start_date,
                                                              end_date)

            load = self.load_computer.compute(flows, concentrations, start_date,
                                              end_date, nutricalc_min)
            load_incremental = self.load_computer.compute(flows, concentrations_incremetal, start_date, end_date,
                                                          nutricalc_incr)


        return load, load_incremental

    def get_impact_timeseries(self,
            start_date, end_date):
        """ Alleen fosfaat op dit moment"""
        logger.debug("WaterbalanceComputer2::get_impact_timeseries")


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

            factor = 1000.0 / float(self.area.surface)

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
        logger.debug("WaterbalanceComputer2::calc_sluice_error_timeseries")

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

            sluice_error = self.sluice_error_computer.compute(
                start_date, end_date,
                [control["intake_wl_control"], control["outtake_wl_control"]],
                ref_intakes.values() + ref_outtakes.values())

            self.outcome['sluice_error'] = sluice_error
            self.outcome_info['sluice_error'] = {}
            self.outcome_info['sluice_error']['start_date'] = start_date
            self.outcome_info['sluice_error']['end_date'] = end_date

            self.updated = True

        return sluice_error

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

            self.outcome['fraction_water'] = fractions
            self.outcome_info['fraction_water'] = {}
            self.outcome_info['fraction_water']['start_date'] = start_date
            self.outcome_info['fraction_water']['end_date'] = end_date

            self.updated = True

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

        for concentr in self.configuration.config_concentrations.all().select_related('Label'):
            if not concentr.label.program_name in concentrations.keys():
                concentrations[concentr.label.program_name] = concentr.cl_concentration

        return concentrations


