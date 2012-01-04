#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The lizard_wbcomputation package implements the computational core of the
# lizard waterbalance Django app.
#
# Copyright (C) 2012 Nelen & Schuurmans
#
# This package is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this package.  If not, see <http://www.gnu.org/licenses/>.

import logging

from lizard_wbcomputation.bucket_computer import BucketOutcome

logger = logging.getLogger(__name__)


class ImpactFromBuckets(object):
    """Implements the calculation of the substance impact time series'.

    The flow off and net drainage of a bucket causes the flow of substances
    into the open water. This class implements the calculation of these
    multiple substance time series.

    """
    def __init__(self, bucket2outcome):
        self.bucket2outcome = bucket2outcome

    def compute(self, start_date, end_date, type, substance):
        bucket2impact = {}
        for bucket, outcome in self.bucket2outcome.items():
            bucket2impact[bucket] = BucketOutcome()
            for event in outcome.flow_off.events(start_date, end_date):
                concentration = event[1] * self.get_concentration(bucket, type, substance)
                bucket2impact[bucket].flow_off.add_value(event[0], concentration)
        return bucket2impact

    def get_concentration(self, bucket, type, substance):
        return getattr(bucket, '%s_concentr_%s_flow_off' % (type, substance))


class SummedImpactFromBuckets(object):
    """Implements the calculation of the substance impact time series'.

    The flow off and net drainage of a bucket causes the flow of substances
    into the open water. This class implements the calculation of these
    multiple substance time series.

    Instance variables:
      *area*
        area for which to compute the substance impact
      *compute_buckets_timeseries*
        function to compute the impact from the timeseries of a BucketOutcome
      *compute_buckets_summary*
        function to compute summary of the BucketOutcome of each bucket
    """
    def __init__(self, area):
        self.area = area

    def compute(self, start_date, end_date, substance_string='phosphate'):

        logger.debug("WaterbalanceComputer2::get_impact_timeseries_from_buckets")

        logger.debug("Calculating impact from buckets(%s - %s)..." % (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')))

        min_impact_timeseries = self.compute_impact_timeseries('min', start_date, end_date, substance_string)
        incr_impact_timeseries = self.compute_impact_timeseries('incr', start_date, end_date, substance_string)

        return min_impact_timeseries, incr_impact_timeseries

    def compute_impact_timeseries(self, type, start_date, end_date, substance_string):

        def update_timeseries(timeseries, area, label):
            timeseries.location_id = area.location_id
            timeseries.parameter_id = label
            timeseries.units = 'mg/m2/dag'
            timeseries.type = 'instantaneous'
            timeseries.miss_val = '-999.0'
            timeseries.station_name = 'Huh?'
            return timeseries

        buckets_timeseries = self.compute_buckets_timeseries(start_date, end_date, type, substance_string)
        buckets_summary = self.compute_buckets_summary(buckets_timeseries, start_date, end_date)

        impact_timeseries = []
        impact_timeseries.append(update_timeseries(getattr(buckets_summary, 'hardened'), self.area, '%s_impact_%s_hardened' % (type, substance_string)))
        impact_timeseries.append(update_timeseries(getattr(buckets_summary, 'drained'), self.area, '%s_impact_%s_drained' % (type, substance_string)))
        impact_timeseries.append(update_timeseries(getattr(buckets_summary, 'flow_off'), self.area, '%s_impact_%s_flow_off' % (type, substance_string)))
        impact_timeseries.append(update_timeseries(getattr(buckets_summary, 'undrained'), self.area, '%s_impact_%s_drainage' % (type, substance_string)))
        impact_timeseries.append(update_timeseries(getattr(buckets_summary, 'sewer'), self.area, '%s_impact_%s_sewer' % (type, substance_string)))
        return impact_timeseries
