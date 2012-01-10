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

from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from mock import Mock

from timeseries.timeseriesstub import SparseTimeseriesStub

from lizard_wbcomputation.bucket_computer import BucketOutcome
from lizard_wbcomputation.bucket_summarizer import BucketsSummarizer
from lizard_wbcomputation.bucket_summarizer import BucketsSummary
from lizard_wbcomputation.bucket_types import BucketTypes
from lizard_wbcomputation.impact_from_buckets import LoadSummary
from lizard_wbcomputation.impact_from_buckets import SummedLoadsFromBuckets

# class ImpactFromBucketsTestSuite(TestCase):

#     def test_a(self):
#         """Test the empty dict is returned when no buckets are present."""
#         bucket_outcomes = {}
#         impact = ImpactFromBuckets(bucket_outcomes)

#         start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)

#         bucket_loads = impact.compute(start, end, 'nitrogen', 'min')
#         self.assertEqual({}, bucket_loads)

    # def test_b(self):
    #     """Test the correct BucketSummary is returned'hardened' loads are computed.

    #     There exists a single bucket with a single event."""

    #     start, end = datetime(2012, 1, 2), datetime(2012, 1, 3)

    #     bucket = Mock()
    #     expected_summary = BucketsSummary()
    #     bucket.compute = lambda s: expected_summary

    #     impact = ImpactFromBuckets({bucket: BucketOutcome()})
    #     summary = impact.compute(start, end, 'nitrogen', 'min')

    #     self.assertEqual(expected_summary, summary)


    # def test_c(self):
    #     """Test the correct dict is returned when two events are present.

    #     There exists a single bucket."""

    #     start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)

    #     bucket = Mock()
    #     bucket.min_concentr_nitrogen_flow_off = 2.0

    #     daily_outcome = BucketOutcome()
    #     daily_outcome.flow_off.add_value(start, 10.0)
    #     daily_outcome.flow_off.add_value(start + timedelta(1), 20.0)
    #     daily_outcome.net_drainage.add_value(start, 30.0)
    #     daily_outcome.net_drainage.add_value(start + timedelta(1), 40.0)

    #     impact = ImpactFromBuckets({bucket: daily_outcome})

    #     type = 'min'
    #     substance = 'nitrogen'
    #     bucket2impact = impact.compute(start, end, substance, type)

    #     self.assertEqual([bucket], bucket2impact.keys())

    #     events = list(bucket2impact[bucket].flow_off.events())
    #     self.assertEqual([(start, 20.0), (start + timedelta(1), 40.0)], events)
    #     events = list(bucket2impact[bucket].net_drainage.events())
    #     self.assertEqual([(start, 60.0), (start + timedelta(1), 80.0)], events)

    # def test_d(self):
    #     """Test the correct dict is returned when two events are present.

    #     There exists a single bucket."""

    #     start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)

    #     bucket = Mock()
    #     bucket.incr_concentr_nitrogen_flow_off = 2.0

    #     daily_outcome = BucketOutcome()
    #     daily_outcome.flow_off.add_value(start, 10.0)
    #     daily_outcome.flow_off.add_value(start + timedelta(1), 20.0)
    #     daily_outcome.net_drainage.add_value(start, 30.0)
    #     daily_outcome.net_drainage.add_value(start + timedelta(1), 40.0)

    #     impact = ImpactFromBuckets({bucket: daily_outcome})

    #     type = 'incr'
    #     substance = 'nitrogen'
    #     bucket2impact = impact.compute(start, end, substance, type)

    #     self.assertEqual([bucket], bucket2impact.keys())

    #     events = list(bucket2impact[bucket].flow_off.events())
    #     self.assertEqual([(start, 20.0), (start + timedelta(1), 40.0)], events)
    #     events = list(bucket2impact[bucket].net_drainage.events())
    #     self.assertEqual([(start, 60.0), (start + timedelta(1), 80.0)], events)


class SummedLoadsFromBucketsTestSuite(TestCase):

    def test_a(self):
        """Test the correct minimum 'hardened' load is computed."""

        summary = BucketsSummary()
        summary.hardened = \
            SparseTimeseriesStub(datetime(2012, 01, 05), [10.0, 20.0])

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        impact = SummedLoadsFromBuckets(start, end, {})
        impact.interesting_attributes = ['hardened']
        impact.compute_summary = lambda substance: (summary, BucketsSummary())

        min_loads, incr_loads = impact.compute('phosphate')

        labels_found = set()
        for load in min_loads:
            if load.label == 'hardened':
               labels_found.add(load.label)
               self.assertEqual(summary.hardened, load.timeseries)
        self.assertEqual(set(['hardened']), labels_found)

    def test_b(self):
        """Test the correct minimum and incremental 'hardened' load is computed."""

        min_summary = BucketsSummary()
        min_summary.hardened = \
            SparseTimeseriesStub(datetime(2012, 01, 05), [10.0, 20.0])
        incr_summary = BucketsSummary()
        incr_summary.hardened = \
            SparseTimeseriesStub(datetime(2012, 01, 05), [30.0, 40.0])

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        impact = SummedLoadsFromBuckets(start, end, {})
        impact.interesting_attributes = ['hardened']
        impact.compute_summary = lambda substance: (min_summary, incr_summary)

        min_loads, incr_loads = impact.compute('phosphate')

        labels_found = set()
        for load in min_loads:
            if load.label == 'hardened':
               labels_found.add(load.label)
               self.assertEqual(min_summary.hardened, load.timeseries)
        self.assertEqual(set(['hardened']), labels_found)

        labels_found = set()
        for load in incr_loads:
            if load.label == 'hardened':
               labels_found.add(load.label)
               self.assertEqual(incr_summary.hardened, load.timeseries)
        self.assertEqual(set(['hardened']), labels_found)

    def test_c(self):
        """Test the correct minimum 'hardened' and 'drained' loads are computed.

        """

        summary = BucketsSummary()
        summary.hardened = \
            SparseTimeseriesStub(datetime(2012, 01, 05), [10.0, 20.0])
        summary.drained = \
            SparseTimeseriesStub(datetime(2012, 01, 05), [30.0, 40.0])

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        impact = SummedLoadsFromBuckets(start, end, {})
        impact.interesting_attributes = ['hardened', 'drained']
        impact.compute_summary = lambda substance: (summary, BucketsSummary())

        min_loads, incr_loads = impact.compute('phosphate')

        labels_found = set()
        for load in min_loads:
            if load.label == 'hardened':
               labels_found.add(load.label)
               self.assertEqual(summary.hardened, load.timeseries)
            if load.label == 'drained':
               labels_found.add(load.label)
               self.assertEqual(summary.drained, load.timeseries)
        self.assertEqual(set(['hardened', 'drained']), labels_found)

    def test_d(self):
        """Test the correct minimum 'hardened' load is computed.

        There is a single bucket.

        """
        def compute_load_summary(outcome, substance, bound):
            summary = BucketsSummary()
            summary.hardened = \
                SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
            return summary

        bucket = Mock()
        bucket.compute_load_summary = compute_load_summary

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 10)
        summary = SummedLoadsFromBuckets(start, end, {bucket: BucketOutcome()})
        summary.interesting_attributes = ['hardened']

        min_summary, inc_summary = summary.compute_summary('phosphate')

        expected_timeseries = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])

        self.assertEqual(expected_timeseries, min_summary.hardened)

    def test_e(self):
        """Test the correct minimum and incremental 'hardened' loads are computed.

        There is a single bucket.

        """
        def compute_load_summary(outcome, substance, bound):
            summary = BucketsSummary()
            if bound == 'min':
                summary.hardened = \
                    SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
            else:
                summary.hardened = \
                    SparseTimeseriesStub(datetime(2012, 1, 9), [0.3, 0.4])
            return summary

        bucket = Mock()
        bucket.compute_load_summary = compute_load_summary

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 9)
        summary = SummedLoadsFromBuckets(start, end, {bucket: BucketOutcome()})
        summary.interesting_attributes = ['hardened']

        min_summary, inc_summary = summary.compute_summary('phosphate')

        min_timeseries, inc_timeseries = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2]), \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.3, 0.4])

        self.assertEqual(min_timeseries, min_summary.hardened)
        self.assertEqual(inc_timeseries, inc_summary.hardened)

    def test_f(self):
        """Test the correct minimum 'hardened' and 'drained' loads are computed.


        There is a single bucket.

        """
        def compute(outcome, substance, bound):
            summary = BucketsSummary()
            summary.hardened = \
                SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
            summary.drained = \
                SparseTimeseriesStub(datetime(2012, 1, 9), [0.3, 0.4])
            return summary

        bucket = Mock()
        bucket.compute_load_summary = compute

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 10)
        summary = SummedLoadsFromBuckets(start, end, {bucket: BucketOutcome()})
        summary.interesting_attributes = ['hardened', 'drained']

        min_summary, inc_summary = summary.compute_summary('phosphate')

        timeseries_hardened = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
        timeseries_drained = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.3, 0.4])

        self.assertEqual(timeseries_hardened, min_summary.hardened)
        self.assertEqual(timeseries_drained, min_summary.drained)

    def test_g(self):
        """Test the correct minimum 'hardened' load is computed.

        There are two buckets.

        """
        def compute(outcome, substance, bound):
            summary = BucketsSummary()
            summary.hardened = \
                SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
            return summary

        bucket2outcome = {}
        bucket = Mock()
        bucket.compute_load_summary = compute
        bucket2outcome[bucket] = BucketOutcome()
        bucket = Mock()
        bucket.compute_load_summary = compute
        bucket2outcome[bucket] = BucketOutcome()
        assert 2 == len(bucket2outcome.keys())

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 10)
        summary = SummedLoadsFromBuckets(start, end, bucket2outcome)
        summary.interesting_attributes = ['hardened']

        min_summary, inc_summary = summary.compute_summary('phosphate')

        expected_timeseries = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.2, 0.4])

        self.assertEqual(expected_timeseries, min_summary.hardened)


class LoadSummaryTestSuite(TestCase):

    def setUp(self):
        self.today = datetime(2012, 1, 9)

    def test_a(self):
        """construction"""
        bucket = Mock()
        bucket.surface_type = BucketTypes.HARDENED_SURFACE
        bucket.min_concentr_phosphate_hardened = 0.2
        outcome = BucketOutcome()
        outcome.flow_off.add_value(self.today, 10.0)
        outcome.net_drainage.add_value(self.today, 20.0)
        start, end = self.today, self.today + timedelta(1)
        summary = LoadSummary(BucketsSummarizer()).compute(start, end, bucket, outcome, 'phosphate', 'min')
        self.assertEqual(summary.hardened, SparseTimeseriesStub(self.today, [-1 * 0.2 * 10.0]))
