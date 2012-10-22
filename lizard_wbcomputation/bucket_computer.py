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
from datetime import datetime

from lizard_wbcomputation.bucket_types import BucketTypes

from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import create_empty_timeseries
from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import multiply_timeseries
from timeseries.timeseriesstub import split_timeseries
from timeseries.timeseriesstub import SparseTimeseriesStub
from timeseries.timeseriesstub import TimeseriesWithMemoryStub

logger = logging.getLogger(__name__)

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

        self.storage = SparseTimeseriesStub()
        self.flow_off = SparseTimeseriesStub()
        self.net_drainage = SparseTimeseriesStub()
        self.seepage = SparseTimeseriesStub()
        self.net_precipitation = SparseTimeseriesStub()

    def name2timeseries(self):
        return {"storage": self.storage,
                "flow_off": self.flow_off,
                "net_drainage": self.net_drainage,
                "seepage": self.seepage,
                "net_precipitation": self.net_precipitation}

    def __dict__(self):
        return {"storage": self.storage,
                "flow_off": self.flow_off,
                "net_drainage": self.net_drainage,
                "seepage": self.seepage,
                "net_precipitation": self.net_precipitation}



def compute_timeseries(bucket, precipitation_ts, evaporation_ts, seepage_ts, fill_below_minimum_with_indraft=True):
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
    previous_volume = bucket['init_water_level'] * bucket['surface'] * bucket['porosity']
    max_volume = bucket['max_water_level'] * bucket['surface'] * bucket['porosity']
    min_volume = bucket['min_water_level'] * bucket['surface'] * bucket['porosity']
    equi_volume = bucket['equi_water_level'] * bucket['surface']


    for triple in enumerate_events(precipitation_ts, evaporation_ts, seepage_ts):
        precipitation = triple[0][1]
        event_date = triple[0][0]
        evaporation = triple[1][1]
        seepage = triple[2][1]

        net_drainage = 0
        net_precipitation = 0
        flow_off = 0


        if previous_volume > equi_volume:
            evaporation_factor = bucket['crop_evaporation_factor']
        else:
            evaporation_factor = bucket['min_crop_evaporation_factor']

        net_precipitation_mmday = precipitation - evaporation * evaporation_factor
        # with regard to the factor 0.001 in the next line, precipitation and
        # evaporation are specified in [mm/day] but surface in [m]: 1 [mm] == 0.001
        # [m]
        net_precipitation = net_precipitation_mmday * bucket['surface'] / 1000.0


        #####compute net drainage#####
        if previous_volume > equi_volume:
            # the net drainage specifies an outgoing volume so should be
            # negative: the drainage fraction is specified as a positive
            # number
            net_drainage = (equi_volume - previous_volume) * bucket['drainage_fraction']
        elif previous_volume < equi_volume:
            # the net drainage specifies an incoming volume so should be
            # postive: the indraft fraction is specified as a positive
            # number
            net_drainage = (equi_volume - previous_volume) * bucket['indraft_fraction']
        else:
            net_drainage = 0

        #####compute seepage#####
        seepage = bucket['surface'] * seepage / 1000.0

        volume = previous_volume + net_precipitation + net_drainage + seepage

        flow_off = 0
        if volume > max_volume:
            flow_off = max_volume - volume
            volume = max_volume
        elif volume < min_volume:
            if fill_below_minimum_with_indraft:
                #todo, check min/plus
                net_drainage += min_volume - volume

            volume = min_volume


        #note that bucket_triple is a quintuple now
        outcome.storage.add_value(event_date, volume)
        outcome.flow_off.add_value(event_date, flow_off)
        outcome.net_drainage.add_value(event_date, net_drainage)
        outcome.seepage.add_value(event_date, seepage)
        outcome.net_precipitation.add_value(event_date, net_precipitation)

        previous_volume = volume

    return outcome

def compute_timeseries_on_undrained_surface(bucket, precipitation, evaporation, seepage):

    # we compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the porosity of the upper bucket is always 1.0
    #   - the storage of the upper bucket can not be below the minimum storage

    bucket_settings = {
        'surface': bucket.surface,
        'porosity': bucket.porosity,
        'crop_evaporation_factor': bucket.crop_evaporation_factor,
        'min_crop_evaporation_factor': bucket.min_crop_evaporation_factor,
        'drainage_fraction':bucket.drainage_fraction,
        'indraft_fraction':bucket.indraft_fraction,
        'max_water_level': bucket.max_water_level,
        'min_water_level': bucket.min_water_level,
        'equi_water_level': bucket.equi_water_level,
        'init_water_level': bucket.init_water_level
    }

    upper_outcome = compute_timeseries(bucket_settings,
                                       precipitation,
                                       evaporation,
                                       seepage,
                                       True)


    return upper_outcome

def compute_timeseries_on_hardened_surface(bucket, precipitation, evaporation, seepage):

    # we compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the porosity of the upper bucket is always 1.0
    #   - the storage of the upper bucket can not be below the minimum storage

    bucket_settings = {
        'surface': bucket.surface,
        'porosity':1.0,
        'crop_evaporation_factor': bucket.crop_evaporation_factor,
        'min_crop_evaporation_factor': bucket.min_crop_evaporation_factor,
        'drainage_fraction':bucket.drainage_fraction,
        'indraft_fraction':bucket.indraft_fraction,
        'max_water_level': bucket.max_water_level,
        'min_water_level': bucket.min_water_level,
        'equi_water_level': bucket.equi_water_level,
        'init_water_level': bucket.init_water_level
    }

    upper_seepage = create_empty_timeseries(seepage)

    upper_outcome = compute_timeseries(bucket_settings,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       False)

    bucket_settings = {
        'surface': bucket.surface,
        'porosity': bucket.bottom_porosity,
        'crop_evaporation_factor': bucket.crop_evaporation_factor,
        'min_crop_evaporation_factor': bucket.min_crop_evaporation_factor,
        'drainage_fraction':bucket.bottom_drainage_fraction,
        'indraft_fraction':bucket.bottom_indraft_fraction,
        'max_water_level': bucket.bottom_max_water_level,
        'min_water_level': bucket.bottom_min_water_level,
        'equi_water_level': bucket.bottom_equi_water_level,
        'init_water_level': bucket.bottom_init_water_level
    }


    # we then compute the lower bucket:
    #  - the lower bucket does not have precipitation, evaporation and does not
    #    have flow off
    lower_precipitation = create_empty_timeseries(precipitation)
    lower_evaporation = create_empty_timeseries(evaporation)

    lower_outcome = compute_timeseries(bucket_settings,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       True)

    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = add_timeseries(lower_outcome.flow_off, lower_outcome.net_drainage)
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation

    return outcome


def compute_timeseries_on_drained_surface(bucket, precipitation, evaporation, seepage):

    # we first compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the upper bucket has some of its own attributes

    bucket_settings = {
        'surface': bucket.surface,
        'porosity':bucket.porosity,
        'crop_evaporation_factor': bucket.crop_evaporation_factor,
        'min_crop_evaporation_factor': bucket.min_crop_evaporation_factor,
        'drainage_fraction':bucket.drainage_fraction,
        'indraft_fraction':bucket.indraft_fraction,
        'max_water_level': bucket.max_water_level,
        'min_water_level': bucket.min_water_level,
        'equi_water_level': bucket.equi_water_level,
        'init_water_level': bucket.init_water_level
    }

    upper_seepage = create_empty_timeseries(seepage)

    upper_outcome = compute_timeseries(bucket_settings,
                                       precipitation,
                                       evaporation,
                                       upper_seepage,
                                       False)

    assert len(list(upper_outcome.flow_off.events())) > 0
    assert len(list(upper_outcome.net_drainage.events())) > 0


    # we compute the lower bucket
    (drainage, indraft) = split_timeseries(upper_outcome.net_drainage)
    # upper_outcome.flow_off and drainage are time series with only
    # non-positive values as they take water away from the upper bucket
    lower_precipitation = drainage
    # As it is, lower_precipitation contains only non-positive values but it
    # adds water to the bottom bucket, so we have to invert these values. Also,
    # lower_precipitation is specified in [m3/day] but should be specified in
    # [mm/day]


    bucket_settings = {
        'surface': bucket.surface,
        'porosity': 1.0, #bucket.bottom_porosity,
        'crop_evaporation_factor': 1.0,
        'min_crop_evaporation_factor': 1.0,
        'drainage_fraction':bucket.bottom_drainage_fraction,
        'indraft_fraction':bucket.bottom_indraft_fraction,
        'max_water_level': bucket.bottom_max_water_level,
        'min_water_level': bucket.bottom_min_water_level,
        'equi_water_level': bucket.bottom_equi_water_level,
        'init_water_level': bucket.bottom_init_water_level
    }

    lower_precipitation = multiply_timeseries(lower_precipitation, -1000.0 / bucket.surface)
    lower_evaporation = create_empty_timeseries(evaporation)
    assert len(list(lower_precipitation.events())) > 0
    lower_outcome = compute_timeseries(bucket_settings,
                                       lower_precipitation,
                                       lower_evaporation,
                                       seepage,
                                       True)

    outcome = BucketOutcome()
    outcome.storage = upper_outcome.storage
    outcome.flow_off = upper_outcome.flow_off
    outcome.net_drainage = add_timeseries(lower_outcome.flow_off, lower_outcome.net_drainage)
    outcome.seepage = lower_outcome.seepage
    outcome.net_precipitation = upper_outcome.net_precipitation
    return outcome


def compute_timeseries_from_sewer(bucket, sewer):

    # we first compute the upper bucket:
    #   - the upper bucket does not have seepage
    #   - the upper bucket has some of its own attributes

    outcome = BucketOutcome()
    outcome.net_drainage = multiply_timeseries(sewer, -1 * bucket.surface/10000)
    return outcome

def compute_timeseries_predefined(bucket):
    """Return the BucketOutcome for the given bucket.

    The given bucket has time series that are defined in the input, viz. one
    time series for flow off and one time series for net drainage.

    """
    outcome = BucketOutcome()
    flow_off = bucket.retrieve_flow_off()
    outcome.flow_off = multiply_timeseries(flow_off, -1.0)
    net_drainage = bucket.retrieve_net_drainage()
    outcome.net_drainage = multiply_timeseries(net_drainage, -1.0)
    return outcome


class BucketComputer:

    def __init__(self, bucket_computers=None):
        if bucket_computers is None:
            self.bucket_computers = {}
            self.bucket_computers[BucketTypes.UNDRAINED_SURFACE] = compute_timeseries_on_undrained_surface
            self.bucket_computers[BucketTypes.HARDENED_SURFACE] = compute_timeseries_on_hardened_surface
            self.bucket_computers[BucketTypes.DRAINED_SURFACE] = compute_timeseries_on_drained_surface
            self.bucket_computers[BucketTypes.STEDELIJK_SURFACE] = compute_timeseries_from_sewer
        else:
            self.bucket_computers = bucket_computers

    def compute(self, bucket, precipitation, evaporation, seepage, sewer=None):
        """Compute and return the BucketOutcome for the given bucket.

        Parameters precipitation, evaporation, seepage and sewer are time
        series.

        """
        logger.debug('calculate bucket outcome for bucket %s', bucket.name)
        if bucket.is_computed:
            surface_type_name = BucketTypes.SURFACE_TYPES[bucket.surface_type]
            if bucket.surface > 0:
                if bucket.surface_type == BucketTypes.STEDELIJK_SURFACE:
                    outcome = compute_timeseries_from_sewer(bucket, sewer)
                else:
                    bucket_computer = self.bucket_computers[bucket.surface_type]
                    outcome = bucket_computer(bucket, precipitation, evaporation, seepage)
                result = outcome
            else:
                logger.warning("bucket has non-positive surface", bucket.name,
                         surface_type_name)
                result = BucketOutcome()
        else:
            logger.debug('bucket outcome for bucket %s is predefined', bucket.name)
            result = compute_timeseries_predefined(bucket)

        return result
