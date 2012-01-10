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
from timeseries.timeseriesstub import multiply_timeseries

from lizard_wbcomputation.bucket_summarizer import BucketsSummary
from lizard_wbcomputation.load_computer import Load

logger = logging.getLogger(__name__)


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
            min_outcome = self.load_summary.compute(bucket, outcome, substance, 'min')
            inc_outcome = self.load_summary.compute(bucket, outcome, substance, 'incr')
            for attribute in self.interesting_labels:
                self._add_timeseries(min_summary, min_outcome, attribute)
                self._add_timeseries(inc_summary, inc_outcome, attribute)
        return min_summary, inc_summary

    def _add_timeseries(self, summary, timeseries, attribute):
        new_timeseries = add_timeseries(getattr(summary, attribute), getattr(timeseries, attribute))
        setattr(summary, attribute, new_timeseries)

    def _create_loads_from_summary(self, summary):
        loads = []
        for attribute in self.interesting_labels:
            load = Load(attribute)
            load.timeseries = getattr(summary, attribute)
            loads.append(load)
        return loads


class LoadSummary(object):

    def __init__(self, buckets_summarizer):
        self.summarizer = buckets_summarizer

    def set_time_range(self, start_date, end_date):
        self.start_date, self.end_date = start_date, end_date

    def compute(self, bucket, outcome, substance, bound):
        self._substance, self._bound = substance, bound
        bucket2outcome = {bucket: outcome}
        summary = self._compute_summary(bucket2outcome)
        return self._compute_load_summary(bucket, summary)

    def _compute_summary(self, bucket2outcome):
        return self.summarizer.compute(bucket2outcome, self.start_date, self.end_date)

    def _compute_load_summary(self, bucket, summary):
        load_summary = BucketsSummary()
        for label in self.interesting_labels:
            timeseries = getattr(summary, label)
            concentration = self._get_concentration(bucket, label)
            load_timeseries = multiply_timeseries(timeseries, concentration)
            setattr(load_summary, label, load_timeseries)
        return load_summary

    def _get_concentration(self, bucket, label):
        attribute = '%s_concentr_%s_%s' % (self._bound, self._substance, label)
        return getattr(bucket, attribute)
