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
from lizard_wbcomputation.load_computer import Load

logger = logging.getLogger(__name__)


class ImpactFromBuckets(object):
    """Implements the calculation of the substance impact time series'.

    The flow off and net drainage of a bucket causes the flow of substances
    into the open water. This class implements the calculation of these
    multiple substance time series.

    """
    def __init__(self, bucket2outcome):
        self.bucket2outcome = bucket2outcome

    def compute(self, start_date, end_date, substance, type):
        bucket2impact = {}
        for bucket, outcome in self.bucket2outcome.items():
            bucket2impact[bucket] = BucketOutcome()
            for event in outcome.flow_off.events(start_date, end_date):
                concentration = event[1] * self.get_concentration(bucket, type, substance)
                bucket2impact[bucket].flow_off.add_value(event[0], concentration)
            for event in outcome.net_drainage.events(start_date, end_date):
                concentration = event[1] * self.get_concentration(bucket, type, substance)
                bucket2impact[bucket].net_drainage.add_value(event[0], concentration)
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
    def __init__(self, start_date, end_date):
        self.start_date, self.end_date = start_date, end_date
        self.interesting_attributes = ['hardened', 'drained', 'undrained', 'flow_off', 'sewer']

    def compute(self, substance='phosphate'):

        minimal = self.compute_loads(substance, 'min')
        incremental = self.compute_loads(substance, 'incr')

        return minimal, incremental

    def compute_loads(self, substance, type):

        bucket2load_timeseries = self.compute_bucket2load_timeseries(
            self.start_date, self.end_date, substance, type)
        buckets_summary = self.compute_buckets_summary(bucket2load_timeseries,
            self.start_date, self.end_date)

        loads = []
        for attribute in self.interesting_attributes:
            load = Load(attribute)
            load.timeseries = getattr(buckets_summary, attribute)
            loads.append(load)

        return loads
