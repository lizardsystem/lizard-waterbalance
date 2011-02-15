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

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.fraction_computer import FractionComputer
from lizard_waterbalance.level_control_computer import LevelControlComputer
from lizard_waterbalance.level_control_storage import LevelControlAssignment
from lizard_waterbalance.level_control_storage import LevelControlStorage
from lizard_waterbalance.vertical_timeseries_computer import VerticalTimeseriesComputer
from lizard_waterbalance.vertical_timeseries_storage import VerticalTimeseriesStorage
from lizard_waterbalance.timeseries import store_waterbalance_timeserie
from lizard_waterbalance.timeseriesstub import add_timeseries
from lizard_waterbalance.timeseriesstub import create_empty_timeseries
from lizard_waterbalance.timeseriesstub import enumerate_events
from lizard_waterbalance.timeseriesstub import multiply_timeseries
from lizard_waterbalance.timeseriesstub import split_timeseries
from lizard_waterbalance.timeseriesstub import subtract_timeseries
from lizard_waterbalance.timeseriesstub import TimeseriesStub
from lizard_waterbalance.timeseriesstub import TimeseriesRestrictedStub


class BucketOutcome:
    """Contains the time series that are computed for a Bucket.

    Instance variables:
      *storage*
        time series for 'berging'
      *flow_off*
        time series for 'afstroming'
      *net_drainage*
        time series for the sum of 'drainage' and 'intrek'
      *seepage*
        time series for 'kwel'
      *net_precipitation*
        time series for the sum of 'neerslag' and 'verdamping'

    The unit of each values of the time series is [m3/day]. A positive value
    indicates water that goes into the bucket and a negative value indicates
    water that goes out of the bucket.

    """
    def __init__(self):

        self.storage = TimeseriesStub()
        self.flow_off = TimeseriesStub()
        self.net_drainage = TimeseriesStub()
        self.seepage = TimeseriesStub()
        self.net_precipitation = TimeseriesStub()

    def name2timeseries(self):
        return {"storage": self.storage,
                "flow_off": self.flow_off,
                "net_drainage": self.net_drainage,
                "seepage": self.seepage,
                "net_precipitation": self.net_precipitation}

class SingleDayBucketsSummary:
    """Stores the interesting values of a single day summed over all buckets.

    Instance variables:
    * hardened -- single day value of in [m3] *Qsom verhard*
    * drained -- single day value in [m3] of *Qsom gedraineerdonder*
    * undrained -- single day value in [m3] of *Qsom ongedraineerd*
    * flow off -- single day value in [m3] of *Qsom afst*
    * indraft -- single day of in [m3] *Qsom intrek*

    """
    def total(self):
        return self.hardened +\
               self.drained +\
               self.undrained +\
               self.flow_off +\
               self.indraft

class BucketsSummary:
    """Stores the total time series computed for all buckets.

    Instance variables:
    * totals -- totals time series in [m3/day] of the other time series
    * hardened -- time series in [m3/day] for *Qsom verhard*
    * drained -- time series in [m3/day] for *Qsom gedraineerdonder*
    * undrained -- time series in [m3/day] for *Qsom ongedraineerd*
    * flow off -- time series in [m3/day] for *Qsom afst*
    * indraft -- time series in [m3/day] for *Qsom intrek*

    """
    def __init__(self):
        self.totals = TimeseriesStub()
        self.hardened = TimeseriesStub()
        self.drained = TimeseriesStub()
        self.undrained = TimeseriesStub()
        self.flow_off = TimeseriesStub()
        self.indraft = TimeseriesStub()

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

def compute_seepage(bucket, seepage):
    """Return the seepage of the given bucket on the given date.

    Parameters:
    * bucket -- bucket for which to compute the seepage
    * date -- date for which to compute the seepage
    * seepage -- seepage in [mm/day]

    """
    # with regard to the factor 0.001 in the next line, seepage is specified
    # in [mm/day] but surface in [m]: 1 [mm] == 0.001 [m]
    return (bucket.surface * seepage) / 1000.0


def compute_net_precipitation(bucket,
                              previous_volume,
                              precipitation,
                              evaporation):
    """Return the net precipitation of today.

    With net precipitation, we mean the volume difference caused by
    precipitation and evaporation.

    Parameters:
    * bucket -- bucket for which to compute the net precipitation
    * previous_volume -- water volume of the bucket the day before
    * precipitation -- precipitation of today in [mm/day]
    * evaporation -- evaporation of today in [mm/day]

    """
    equi_volume = bucket.equi_water_level * bucket.surface
    if previous_volume > equi_volume:
        evaporation_factor = bucket.crop_evaporation_factor
    else:
        evaporation_factor = bucket.min_crop_evaporation_factor

    net_precipitation = precipitation - evaporation * evaporation_factor
    # with regard to the factor 0.001 in the next line, precipitation and
    # evaporation are specified in [mm/day] but surface in [m]: 1 [mm] == 0.001
    # [m]
    return net_precipitation * bucket.surface / 1000.0


def compute_net_drainage(bucket, previous_volume):
    """Return the net drainage of today.

    With net drainage, we mean the volume difference caused by drainage and
    indraft.

    Parameters:
    * bucket -- bucket for which to compute the net drainage
    * previous_volume -- water volume of the bucket the day before

    """
    equi_volume = bucket.equi_water_level * bucket.surface
    if previous_volume > equi_volume:
        net_drainage = -previous_volume * bucket.drainage_fraction
    elif previous_volume < equi_volume:
        net_drainage = -previous_volume * bucket.indraft_fraction
    else:
        net_drainage = 0
    return net_drainage

def compute(bucket, previous_storage, precipitation, evaporation, seepage, allow_below_minimum_storage=True):
    """Compute and return the waterbalance of the given bucket.

    This method computes for the given bucket the water storage, flow off, net
    drainage, seepage and net precipitation and returns them as a quintuple.

    Parameters:
    * bucket -- bucket for which to compute the waterbalance
    * previous_storage -- water storage of the bucket the day before in [m3]
    * precipitation -- precipitation time series for the bucket in [mm/day]
    * evaporation -- evaporation time series for the bucket in [mm/day]
    * seepage -- seepage time series for the bucket in [mm/day]
    * allow_below_minimum_storage -- holds iff the computed storage can be below the minimum storage

    """
    net_precipitation = compute_net_precipitation(bucket, previous_storage,
                                                  precipitation, evaporation)
    net_drainage = compute_net_drainage(bucket, previous_storage)
    seepage = compute_seepage(bucket, seepage)

    storage = previous_storage + net_precipitation + net_drainage + seepage
    max_storage = bucket.max_water_level * bucket.surface * bucket.porosity
    if storage > max_storage:
        flow_off = max_storage - storage
        storage = max_storage
    else:
        flow_off = 0

    if not allow_below_minimum_storage:
        storage = max(storage, bucket.min_water_level * bucket.surface)

    return (storage, flow_off, net_drainage, seepage, net_precipitation)

def compute_timeseries(bucket, precipitation, evaporation, seepage, compute, allow_below_minimum_storage=True):
    """Compute and return the waterbalance time series of the given bucket.

    This method computes for the given bucket the time series that can be
    stored in a BucketOutcome and returns them as a BucketOutcome.

    Parameters:
    * bucket -- bucket for which to compute the waterbalance
    * precipitation -- precipitation time series in [mm/day]
    * evaporation -- evaporation time series  in [mm/day]
    * seepage -- seepage time series in [mm/day]
    * compute -- function to compute the daily waterbalance
    * allow_below_minimum_storage -- holds iff the computed storage can be below the minimum storage

    """
    outcome = BucketOutcome()
    volume = bucket.init_water_level * bucket.surface
    for triple in enumerate_events(precipitation, evaporation, seepage):
        precipitation_event = triple[0]
        event_date = precipitation_event[0]
        evaporation_event = triple[1]
        seepage_event = triple[2]
        bucket_triple = compute(bucket, volume, precipitation_event[1],
                                evaporation_event[1], seepage_event[1],
                                allow_below_minimum_storage)
        #note that bucket_triple is a quintuple now
        volume = bucket_triple[0]
        outcome.storage.add_value(event_date, volume)
        outcome.flow_off.add_value(event_date, bucket_triple[1])
        outcome.net_drainage.add_value(event_date, bucket_triple[2])
        outcome.seepage.add_value(event_date, bucket_triple[3])
        outcome.net_precipitation.add_value(event_date, bucket_triple[4])
    return outcome

def compute_timeseries_on_hardened_surface(bucket, precipitation, evaporation, seepage, compute):

    # we compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the porosity of the upper bucket is always 1.0
    #   - the storage of the upper bucket can not be below the minimum storage

    upper_seepage = create_empty_timeseries(seepage)
    bucket.porosity, tmp = 1.0, bucket.porosity
    bucket.drainage_fraction, bucket.upper_drainage_fraction = \
                              bucket.upper_drainage_fraction, bucket.drainage_fraction
    bucket.indraft_fraction, bucket.upper_indraft_fraction = \
                              bucket.upper_indraft_fraction, bucket.indraft_fraction
    upper_outcome = compute_timeseries(bucket,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       compute,
                                       False)
    bucket.drainage_fraction, bucket.upper_drainage_fraction = \
                              bucket.upper_drainage_fraction, bucket.drainage_fraction
    bucket.indraft_fraction, bucket.upper_indraft_fraction = \
                              bucket.upper_indraft_fraction, bucket.indraft_fraction
    bucket.porosity = tmp

    # we then compute the lower bucket:
    #  - the lower bucket does not have precipitation, evaporation and does not
    #    have flow off
    lower_precipitation = create_empty_timeseries(precipitation)
    lower_evaporation = create_empty_timeseries(evaporation)
    lower_outcome = compute_timeseries(bucket,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       compute)
    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = add_timeseries(lower_outcome.flow_off, lower_outcome.net_drainage)
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation
    return outcome


def compute_timeseries_on_drained_surface(bucket, precipitation, evaporation, seepage, compute):

    # we first compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the upper bucket has some of its own attributes
    upper_seepage = create_empty_timeseries(seepage)

    bucket.porosity, bucket.upper_porosity = bucket.upper_porosity, bucket.porosity
    bucket.crop_evaporation_factor, bucket.upper_crop_evaporation_factor = bucket.upper_crop_evaporation_factor, bucket.crop_evaporation_factor
    bucket.min_crop_evaporation_factor, bucket.upper_min_crop_evaporation_factor = bucket.upper_min_crop_evaporation_factor, bucket.min_crop_evaporation_factor
    bucket.drainage_fraction, bucket.upper_drainage_fraction = \
                              bucket.upper_drainage_fraction, bucket.drainage_fraction
    bucket.indraft_fraction, bucket.upper_indraft_fraction = \
                              bucket.upper_indraft_fraction, bucket.indraft_fraction
    upper_outcome = compute_timeseries(bucket,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       compute)
    assert len(list(upper_outcome.flow_off.events())) > 0
    assert len(list(upper_outcome.net_drainage.events())) > 0
    bucket.porosity, bucket.upper_porosity = bucket.upper_porosity, bucket.porosity
    bucket.crop_evaporation_factor, bucket.upper_crop_evaporation_factor = bucket.upper_crop_evaporation_factor, bucket.crop_evaporation_factor
    bucket.min_crop_evaporation_factor, bucket.upper_min_crop_evaporation_factor = bucket.upper_min_crop_evaporation_factor, bucket.min_crop_evaporation_factor
    bucket.drainage_fraction, bucket.upper_drainage_fraction = \
                              bucket.upper_drainage_fraction, bucket.drainage_fraction
    bucket.indraft_fraction, bucket.upper_indraft_fraction = \
                              bucket.upper_indraft_fraction, bucket.indraft_fraction

    # we compute the lower bucket
    (drainage, indraft) = split_timeseries(upper_outcome.net_drainage)
    # upper_outcome.flow_off and drainage are time series with only
    # non-positive values as they take water away from the upper bucket
    lower_precipitation = add_timeseries(upper_outcome.flow_off, drainage)
    # As it is, lower_precipitation contains only non-positive values but it
    # adds water to the bottom bucket, so we have to invert these values. Also,
    # lower_precipitation is specified in [m3/day] but should be specified in
    # [mm/day]
    lower_precipitation = multiply_timeseries(lower_precipitation, -1000.0 / bucket.surface)
    lower_evaporation = create_empty_timeseries(evaporation)
    assert len(list(lower_precipitation.events())) > 0
    lower_outcome = compute_timeseries(bucket,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       compute)
    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = lower_outcome.net_drainage
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation
    return outcome


def retrieve_net_intake(open_water):

    incoming_timeseries = TimeseriesStub()
    for timeseries in open_water.retrieve_incoming_timeseries():
        incoming_timeseries = add_timeseries(incoming_timeseries, timeseries)

    outgoing_timeseries = TimeseriesStub()
    for timeseries in open_water.retrieve_outgoing_timeseries():
        outgoing_timeseries = add_timeseries(outgoing_timeseries, timeseries)

    return subtract_timeseries(incoming_timeseries, outgoing_timeseries)


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
        self.store_timeserie = store_timeserie
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

        self.pumping_station2timeseries = {}

    def compute(self, area, start_date, end_date):
        """Compute the waterbalance-related time series for the given area.

        Args:
          *area*
            WaterbalanceArea for which to compute the time series
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

        precipitation = area.retrieve_precipitation(start_date, end_date)
        evaporation = area.retrieve_evaporation(start_date, end_date)
        seepage = area.retrieve_seepage(start_date, end_date)
        buckets = area.retrieve_buckets()
        bucket2outcome = self.buckets_computer.compute(buckets,
                                                       precipitation,
                                                       evaporation,
                                                       seepage)

        buckets_summary = self.buckets_summarizer.compute(bucket2outcome)

        self.store_timeserie(area.open_water, "undrained",
                                     buckets_summary.undrained)
        self.store_timeserie(area.open_water, "drained",
                                     buckets_summary.drained)
        self.store_timeserie(area.open_water, "hardened",
                                     buckets_summary.hardened)
        self.store_timeserie(area.open_water, "flow_off",
                                     buckets_summary.flow_off)
        self.store_timeserie(area.open_water, "indraft",
                                     buckets_summary.indraft)

        outcome.open_water_timeseries = {"undrained": buckets_summary.undrained,
                                         "drained": buckets_summary.drained,
                                         "hardened": buckets_summary.hardened,
                                         "flow_off": buckets_summary.flow_off,
                                         "indraft": buckets_summary.indraft}

        vertical_timeseries = self.vertical_timeseries_computer.compute(area.open_water.surface,
                                                                        area.open_water.crop_evaporation_factor,
                                                                        precipitation,
                                                                        evaporation,
                                                                        seepage)
        self.vertical_timeseries_storage.store(vertical_timeseries,
                                               area.open_water)

        outcome.open_water_timeseries["precipitation"] = vertical_timeseries[0]
        outcome.open_water_timeseries["evaporation"] = vertical_timeseries[1]
        outcome.open_water_timeseries["seepage"] = vertical_timeseries[2]
        outcome.open_water_timeseries["infiltration"] = vertical_timeseries[3]

        incoming_timeseries = []
        for timeseries in self.retrieve_incoming_timeseries(area.open_water):
            incoming_timeseries.append(TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date))

        outgoing_timeseries = []
        for timeseries in area.open_water.retrieve_outgoing_timeseries(only_input=True):
            outgoing_timeseries.append(TimeseriesRestrictedStub(timeseries=timeseries,
                                                                start_date=start_date,
                                                                end_date=end_date))

        minimum_level_timeseries = TimeseriesRestrictedStub(timeseries=area.open_water.retrieve_minimum_level(),
                                                            start_date=start_date,
                                                            end_date=end_date)

        maximum_level_timeseries = TimeseriesRestrictedStub(timeseries=area.open_water.retrieve_maximum_level(),
                                                            start_date=start_date,
                                                            end_date=end_date)

        level_control = self.level_control_computer.compute(area.open_water,
                                                            buckets_summary,
                                                            vertical_timeseries,
                                                            minimum_level_timeseries,
                                                            maximum_level_timeseries,
                                                            incoming_timeseries,
                                                            outgoing_timeseries)

        pumping_stations = area.open_water.pumping_stations.all()
        outcome.level_control_assignment = self.level_control_assignment.compute(level_control[0:2],
                                                           pumping_stations)
        self.level_control_storage.store(pumping_stations, outcome.level_control_assignment)

        outcome.open_water_timeseries["storage"] = level_control[2]
        self.store_timeserie(area.open_water, "storage", outcome.open_water_timeseries["storage"])

        intakes, tmp_timeseries = self.retrieve_intakes_timeseries(area.open_water)
        intakes_timeseries = [TimeseriesRestrictedStub(timeseries=timeseries,
                                                       start_date=start_date,
                                                       end_date=end_date) for timeseries in tmp_timeseries]
        fractions = self.fraction_computer.compute(area.open_water,
                                                   buckets_summary,
                                                   vertical_timeseries,
                                                   outcome.open_water_timeseries["storage"],
                                                   intakes_timeseries)

        self.store_timeserie(area.open_water, "fractions_initial",
                             fractions[0])
        outcome.open_water_fractions["initial"] = fractions[0]
        self.store_timeserie(area.open_water, "fractions_precipitation",
                             fractions[1])
        outcome.open_water_fractions["precipitation"] = fractions[1]
        self.store_timeserie(area.open_water, "fractions_seepage",
                             fractions[2])
        outcome.open_water_fractions["seepage"] = fractions[2]
        self.store_timeserie(area.open_water, "fractions_hardened",
                             fractions[3])
        outcome.open_water_fractions["hardened"] = fractions[3]
        self.store_timeserie(area.open_water, "fractions_drained",
                             fractions[4])
        outcome.open_water_fractions["drained"] = fractions[4]
        self.store_timeserie(area.open_water, "fractions_undrained",
                             fractions[5])
        outcome.open_water_fractions["undrained"] = fractions[5]
        self.store_timeserie(area.open_water, "fractions_flow_off",
                             fractions[6])
        outcome.open_water_fractions["flow_off"] = fractions[6]
        for index, intake in enumerate(intakes):
            self.store_timeserie(intake, "fractions", fractions[7 + index])
            intake.save()
            outcome.intake_fractions[intake] = fractions[7 + index]

        area.open_water.save()

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
                if pumping_station.computed_level_control:
                    if pumping_station.level_control is None:
                        timeseries = TimeseriesStub()
                    else:
                        timeseries = pumping_station.level_control.volume
                else:
                    # big ugly hack
                    if self.pumping_station2timeseries:
                        timeseries = self.pumping_station2timeseries[pumping_station.name] # pumping_station.retrieve_timeseries()
                        self.store_timeserie(pumping_station, "reference", timeseries)
                        pumping_station.save()
                    else:
                        timeseries = pumping_station.retrieve_timeseries()
                intakes_timeseries.append(timeseries)
        return intakes, intakes_timeseries

    def retrieve_incoming_timeseries(self, open_water):
        """Return the volume timeseries of the intakes with a fixed throughput.

        Parameter:
        * open_water -- OpenWater to which the intakes belong
        """
        incoming_timeseries = []
        intakes, intakes_timeseries = self.retrieve_intakes_timeseries(open_water)
        for intake, timeseries in zip(intakes, intakes_timeseries):
            if intake.into and not intake.computed_level_control:
                incoming_timeseries.append(timeseries)
        return incoming_timeseries


class BucketsComputer:

    def __init__(self, bucket_computers=None):
        if bucket_computers is None:
            self.bucket_computers = {}
            self.bucket_computers[Bucket.UNDRAINED_SURFACE] = compute_timeseries
            self.bucket_computers[Bucket.HARDENED_SURFACE] = compute_timeseries_on_hardened_surface
            self.bucket_computers[Bucket.DRAINED_SURFACE] = compute_timeseries_on_drained_surface
        else:
            self.bucket_computers = bucket_computers

    def compute(self, buckets, precipitation, evaporation, seepage):
        """Compute and return the waterbalance for the given buckets.

        Parameters:
        * buckets -- list of buckets connected to the open water
        * precipitation -- TimesseriesStub for the precipitation
        * evaporation -- TimesseriesStub for the evaporation
        * seepage -- TimesseriesStub for the seepage

        Return value:
        * result -- dictionary of bucket to TimesseriesStub
        """
        result = {}
        for bucket in buckets:
            bucket_computer = self.bucket_computers[bucket.surface_type]
            outcome = bucket_computer(bucket, precipitation, evaporation, seepage, compute)
            result[bucket] = outcome
        return result


def event_tuple_values(events):
    """Return the list of event values from the given tuple of events."""
    return [event[1] for event in events]

def create_bucket_to_daily_outcome(buckets, daily_outcome):
    assert len(buckets) * 2 == len(daily_outcome)
    index = 0
    bucket2daily_outcome = {}
    for bucket in buckets:
        bucket2daily_outcome[bucket] = [daily_outcome[index * 2], daily_outcome[index * 2 + 1]]
        index = index + 1
    return bucket2daily_outcome

def total_daily_bucket_outcome(bucket2outcome):
    """Return the total daily flow off and net drainage of all buckets

    Parameters:
    * bucket2outcome -- dictionary of Bucket to BucketOutcome

    """
    generator = ()
    if len(bucket2outcome.keys()) > 0:
        buckets, outcomes = zip(*((b, o) for (b, o) in bucket2outcome.items()))
        interesting_timeseries = []
        for outcome in outcomes:
            interesting_timeseries.append(outcome.flow_off)
            interesting_timeseries.append(outcome.net_drainage)
        generator = ((event_tuple[0][0], create_bucket_to_daily_outcome(buckets, event_tuple_values(event_tuple))) \
                     for event_tuple in enumerate_events(*interesting_timeseries))
    return generator


class BucketSummarizer:
    """Computes the SingleDayBucketsSummary.

    Instance variables:
    * bucket2daily_outcome -- dictionary of Bucket to BucketOutcome
    """
    def __init__(self, bucket2daily_outcome={}):
        """Set the dictionary of Bucket to BucketOutcome to the given one."""
        self.bucket2daily_outcome = bucket2daily_outcome

    def compute(self):
        """Compute and return the SingleDayBucketsSummary."""
        summary = SingleDayBucketsSummary()

        # Note that the time series computed for each bucket are computed from
        # the point of view the bucket:
        #   - a positive total means water flows to the buckets from the open
        #     water
        #   - a negative value means water flows from the buckets to the open
        #     water
        # So to get the volume that flows from the buckets to the open water we
        # have to negate the bucket total.

        summary.hardened = -self.compute_sum_hardened()
        summary.drained = -self.compute_sum_drained()
        summary.undrained = -self.compute_sum_undrained_net_drainage()
        summary.flow_off = -self.compute_sum_undrained_flow_off()
        summary.indraft = -self.compute_sum_indraft()
        summary.totals = summary.hardened + \
                         summary.drained + \
                         summary.undrained + \
                         summary.flow_off + \
                         summary.indraft
        return summary

    def compute_sum_hardened(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == Bucket.HARDENED_SURFACE:
                sum += outcome[0]
        return sum

    def compute_sum_drained(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == Bucket.DRAINED_SURFACE:
                sum += outcome[0]
                net_drainage = outcome[1]
                if net_drainage < 0:
                    sum += net_drainage
        return sum

    def compute_sum_undrained_net_drainage(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == Bucket.HARDENED_SURFACE or \
               bucket.surface_type == Bucket.UNDRAINED_SURFACE:
                net_drainage = outcome[1]
                if net_drainage < 0:
                    sum += net_drainage
        return sum

    def compute_sum_undrained_flow_off(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == Bucket.UNDRAINED_SURFACE:
                sum += outcome[0]
        return sum

    def compute_sum_indraft(self):
        sum = 0.0
        for bucket, outcome in self.bucket2daily_outcome.iteritems():
            if bucket.surface_type == Bucket.UNDRAINED_SURFACE or \
               bucket.surface_type == Bucket.HARDENED_SURFACE or \
               bucket.surface_type == Bucket.DRAINED_SURFACE:
                net_drainage = outcome[1]
                if net_drainage > 0:
                    sum += net_drainage
        return sum


class BucketsSummarizer:
    """Computes the BucketSummary from the outcome of each bucket."""
    def compute(self, bucket2outcome):
        """Returns the BucketsSummary of the given buckets.

        Parameters:
        * bucket2outcome --dictionary of Bucket to BucketOutcome

        """
        buckets_summary = BucketsSummary()
        for date, bucket2daily_outcome in total_daily_bucket_outcome(bucket2outcome):
            daily_summary = BucketSummarizer(bucket2daily_outcome).compute()
            buckets_summary.totals.add_value(date, daily_summary.total())
            buckets_summary.hardened.add_value(date, daily_summary.hardened)
            buckets_summary.drained.add_value(date, daily_summary.drained)
            buckets_summary.undrained.add_value(date, daily_summary.undrained)
            buckets_summary.flow_off.add_value(date, daily_summary.flow_off)
            buckets_summary.indraft.add_value(date, daily_summary.indraft)
        return buckets_summary
