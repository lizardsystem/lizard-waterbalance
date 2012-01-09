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

from timeseries.timeseriesstub import add_timeseries

from lizard_wbcomputation.bucket_computer import BucketOutcome
from lizard_wbcomputation.bucket_summarizer import BucketsSummary
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


class SummedLoadsFromBuckets(object):
    """Implements the calculation of the summed bucket loads.

    """
    def __init__(self, start_date, end_date, bucket2outcome):
        self.start_date, self.end_date = start_date, end_date
        self.bucket2outcome = bucket2outcome

    def compute(self, substance):
        min_summary, inc_summary = self.compute_summary(substance)
        min_loads = self._create_loads_from_summary(min_summary)
        inc_loads = self._create_loads_from_summary(inc_summary)
        return min_loads, inc_loads

    def compute_summary(self, substance):
        """Compute and return the minimum and incremental the bucket loads.

        This method returns a tuple of two BucketsSummary(s), where the first
        summary contains the minimum bucket loads and the second the
        incremental bucket loads.

        The parameter specifies the substance for which to compute the load.

        """
        min_summary = BucketsSummary()
        inc_summary = BucketsSummary()
        for bucket, outcome in self.bucket2outcome.items():
            min_outcome = bucket.compute_load_summary(outcome, substance, 'min')
            inc_outcome = bucket.compute_load_summary(outcome, substance, 'inc')
            for attribute in self.interesting_attributes:
                self._add_timeseries(min_summary, min_outcome, attribute)
                self._add_timeseries(inc_summary, inc_outcome, attribute)
        return min_summary, inc_summary

    def _add_timeseries(self, summary, timeseries, attribute):

        new_timeseries = add_timeseries(getattr(summary, attribute), getattr(timeseries, attribute))
        setattr(summary, attribute, new_timeseries)

    def _create_loads_from_summary(self, summary):
        loads = []
        for attribute in self.interesting_attributes:
            load = Load(attribute)
            load.timeseries = getattr(summary, attribute)
            loads.append(load)
        return loads


class SummaryComputer(object):

    def __init__(self, bucket2outcome):
        self.bucket2outcome = bucket2outcome

    def compute(self, substance):
        """Compute and return the minimum and incremental the bucket loads.

        This method returns a tuple of two BucketsSummary(s), where the first
        summary contains the minimum bucket loads and the second the
        incremental bucket loads.

        The parameter specifies the substance for which to compute the load.

        """
        min_summary = BucketsSummary()
        inc_summary = BucketsSummary()
        for bucket, outcome in self.bucket2outcome.items():
            min_outcome = bucket.compute_load_summary(outcome, substance, 'min')
            inc_outcome = bucket.compute_load_summary(outcome, substance, 'inc')
            for attribute in self.interesting_attributes:
                self.add_timeseries(min_summary, min_outcome, attribute)
                self.add_timeseries(inc_summary, inc_outcome, attribute)

        return min_summary, inc_summary

    def add_timeseries(self, summary, timeseries, attribute):

        new_timeseries = add_timeseries(getattr(summary, attribute), getattr(timeseries, attribute))
        setattr(summary, attribute, new_timeseries)

