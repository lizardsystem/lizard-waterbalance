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
# Initial date:       ????-??-??
#
#******************************************************************************

import logging

from lizard_waterbalance.models import Bucket

from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import create_empty_timeseries
from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import multiply_timeseries
from timeseries.timeseriesstub import split_timeseries
from timeseries.timeseriesstub import subtract_timeseries
from timeseries.timeseriesstub import TimeseriesStub
from timeseries.timeseriesstub import TimeseriesRestrictedStub
from timeseries.timeseriesstub import TimeseriesWithMemoryStub


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


def empty_outcome(start_date):
    """returns bucket_outcome with timeseries with memory, with a first value of 0

    """
    outcome = BucketOutcome()
    
    outcome.storage = TimeseriesWithMemoryStub()
    outcome.flow_off = TimeseriesWithMemoryStub()
    outcome.net_drainage = TimeseriesWithMemoryStub()
    outcome.seepage = TimeseriesWithMemoryStub()
    outcome.net_precipitation = TimeseriesWithMemoryStub()
    
    outcome.storage.add_value(start_date, 0)
    outcome.flow_off.add_value(start_date, 0)
    outcome.net_drainage.add_value(start_date, 0)
    outcome.seepage.add_value(start_date, 0)
    outcome.net_precipitation.add_value(start_date, 0)
        
    return outcome 
        
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
        net_drainage = -previous_volume * bucket.indraft_fraction #klopt het minteken?
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
    volume = bucket.init_water_level * bucket.surface * bucket.porosity
    
    if not allow_below_minimum_storage and bucket.min_water_level == None:
        print "Warning, minimum level is not set for %s, default value 0 taken for calculation (level below minimum level is not allowed for this bucket type)"%bucket.name    
        bucket.min_water_level = 0
        
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

def switch_values(one, two):
    return two, one

def switch_bucket_upper_values(bucket):
    
    bucket.porosity, bucket.upper_porosity = switch_values(bucket.porosity, bucket.upper_porosity)
    bucket.drainage_fraction, bucket.upper_drainage_fraction = switch_values(bucket.drainage_fraction, bucket.upper_drainage_fraction)
    bucket.indraft_fraction, bucket.upper_indraft_fraction = switch_values(bucket.indraft_fraction, bucket.upper_indraft_fraction)
    bucket.max_water_level, bucket.upper_max_water_level = switch_values(bucket.max_water_level, bucket.upper_max_water_level)
    bucket.min_water_level, bucket.upper_min_water_level = switch_values(bucket.min_water_level, bucket.upper_min_water_level)
    bucket.init_water_level, bucket.upper_init_water_level = switch_values(bucket.init_water_level, bucket.upper_init_water_level)
    return bucket

def compute_timeseries_on_hardened_surface(bucket, precipitation, evaporation, seepage, compute):

    # we compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the porosity of the upper bucket is always 1.0
    #   - the storage of the upper bucket can not be below the minimum storage

    upper_seepage = create_empty_timeseries(seepage)
    
    
    bucket = switch_bucket_upper_values(bucket)
    bucket.porosity, tmp = 1.0, bucket.porosity
    
    upper_outcome = compute_timeseries(bucket,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       compute,
                                       False)
    bucket.porosity = tmp
    bucket = switch_bucket_upper_values(bucket)

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

    bucket = switch_bucket_upper_values(bucket)
    
    upper_outcome = compute_timeseries(bucket,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       compute)
    assert len(list(upper_outcome.flow_off.events())) > 0
    assert len(list(upper_outcome.net_drainage.events())) > 0
    
    bucket = switch_bucket_upper_values(bucket)

    # we compute the lower bucket
    (drainage, indraft) = split_timeseries(upper_outcome.net_drainage)
    # upper_outcome.flow_off and drainage are time series with only
    # non-positive values as they take water away from the upper bucket
    lower_precipitation = add_timeseries(upper_outcome.flow_off, drainage)
    # As it is, lower_precipitation contains only non-positive values but it
    # adds water to the bottom bucket, so we have to invert these values. Also,
    # lower_precipitation is specified in [m3/day] but should be specified in
    # [mm/day]

    bucket.crop_evaporation_factor, tmp_crop_evaporation = 1, bucket.crop_evaporation_factor
    bucket.min_crop_evaporation_factor, tmp_min_crop_evaporation = 1 , bucket.min_crop_evaporation_factor
    lower_precipitation = multiply_timeseries(lower_precipitation, -1000.0 / bucket.surface)
    lower_evaporation = create_empty_timeseries(evaporation)
    assert len(list(lower_precipitation.events())) > 0
    lower_outcome = compute_timeseries(bucket,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       compute)

    bucket.crop_evaporation_factor = tmp_crop_evaporation
    bucket.min_crop_evaporation_factor = tmp_min_crop_evaporation

    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = add_timeseries(lower_outcome.flow_off, lower_outcome.net_drainage)
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation
    return outcome


class BucketsComputer:

    def __init__(self, bucket_computers=None):
        if bucket_computers is None:
            self.bucket_computers = {}
            self.bucket_computers[Bucket.UNDRAINED_SURFACE] = compute_timeseries
            self.bucket_computers[Bucket.STEDELIJK_SURFACE] = compute_timeseries
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
            if bucket.surface > 0:
                print bucket.name
                print bucket.surface_type
                bucket_computer = self.bucket_computers[bucket.surface_type]
                outcome = bucket_computer(bucket, precipitation, evaporation, seepage, compute)
                
                result[bucket] = outcome
            else:
                result[bucket] = empty_outcome(precipitation.start_date) #mooier is een functie_get startdate
        return result
