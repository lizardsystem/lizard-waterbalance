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


class SummedLoadsFromBuckets_compute_TestSuite(TestCase):
    """Implements a test suite for method SummedLoadsFromBuckets::compute.

    These tests substitute hard code method compute_summary to test method
    compute in isolation.

    """

    def test_a(self):
        """Test the correct minimum loads are computed."""
        summed_loads = self.create_summed_loads()
        summed_loads.interesting_labels = ['hardened']

        min_loads, incr_loads = summed_loads.compute('phosphate')

        self.loads_contain_labels(min_loads, ['hardened'])
        self.loads_contain_timeseries(min_loads, 'hardened', self.min_summary.hardened)

    def create_summed_loads(self):
        start, end, bucket2outcome = None, None, {} # don't care
        summed_loads = SummedLoadsFromBuckets(start, end, bucket2outcome)
        summed_loads.compute_summary = self.create_compute_summary()
        return summed_loads

    def create_compute_summary(self):
        date = datetime(2012, 1, 5)
        min_summary = BucketsSummary()
        inc_summary = BucketsSummary()
        min_summary.hardened = SparseTimeseriesStub(date, [10.0, 20.0])
        inc_summary.hardened = SparseTimeseriesStub(date, [30.0, 40.0])
        min_summary.drained = SparseTimeseriesStub(date, [30.0, 40.0])
        self.min_summary = min_summary
        self.inc_summary = inc_summary
        return lambda substance: (min_summary, inc_summary)

    def loads_contain_labels(self, loads, expected_labels):
        """Return True iff each load has an expected label."""
        labels = set((l.label for l in loads if l.label in expected_labels))
        self.assertEqual(set(expected_labels), labels)

    def loads_contain_timeseries(self, loads, label, timeseries):
        """Return True iff each specified load contains the given time series.

        The specified load is the load with the given label.

        """
        for load in loads:
            if load.label == label:
               self.assertEqual(timeseries, load.timeseries)

    def test_b(self):
        """Test the correct minimum and incremental 'hardened' load is computed."""
        summed_loads = self.create_summed_loads()
        summed_loads.interesting_labels = ['hardened']

        min_loads, inc_loads = summed_loads.compute('phosphate')

        self.loads_contain_labels(min_loads, ['hardened'])
        self.loads_contain_timeseries(min_loads, 'hardened', self.min_summary.hardened)

        self.loads_contain_labels(inc_loads, ['hardened'])
        self.loads_contain_timeseries(inc_loads, 'hardened', self.inc_summary.hardened)

    def test_c(self):
        """Test the correct minimum 'hardened' and 'drained' loads are computed.

        """
        summed_loads = self.create_summed_loads()
        summed_loads.interesting_labels = ['hardened', 'drained']

        min_loads, inc_loads = summed_loads.compute('phosphate')

        self.loads_contain_labels(min_loads, ['hardened', 'drained'])
        self.loads_contain_timeseries(min_loads, 'hardened', self.min_summary.hardened)
        self.loads_contain_timeseries(min_loads, 'drained', self.min_summary.drained)

        self.loads_contain_labels(inc_loads, ['hardened', 'drained'])
        self.loads_contain_timeseries(inc_loads, 'hardened', self.inc_summary.hardened)
        self.loads_contain_timeseries(inc_loads, 'drained', self.inc_summary.drained)


class SummedLoadsFromBucketsTestSuite(TestCase):

    def test_d(self):
        """Test the correct minimum 'hardened' load is computed.

        There is a single bucket.

        """
        class StubLoadSummary(object):

            def compute(self, bucket, outcome, substance, bound):
                summary = BucketsSummary()
                summary.hardened = \
                    SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
                return summary

        load_summary = StubLoadSummary()

        bucket = Mock()

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 10)
        summary = SummedLoadsFromBuckets(start, end, {bucket: BucketOutcome()})
        summary.interesting_labels = ['hardened']
        summary.load_summary = load_summary

        min_summary, inc_summary = summary.compute_summary('phosphate')

        expected_timeseries = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])

        self.assertEqual(expected_timeseries, min_summary.hardened)

    def test_e(self):
        """Test the correct minimum and incremental 'hardened' loads are computed.

        There is a single bucket.

        """
        class StubLoadSummary(object):

            def compute(self, bucket, outcome, substance, bound):
                summary = BucketsSummary()
                if bound == 'min':
                    summary.hardened = \
                        SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
                else:
                    summary.hardened = \
                        SparseTimeseriesStub(datetime(2012, 1, 9), [0.3, 0.4])
                return summary

        bucket = Mock()

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 9)
        summary = SummedLoadsFromBuckets(start, end, {bucket: BucketOutcome()})
        summary.interesting_labels = ['hardened']
        summary.load_summary = StubLoadSummary()

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
        class StubLoadSummary(object):

            def compute(self, bucket, outcome, substance, bound):
                summary = BucketsSummary()
                summary.hardened = \
                    SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
                summary.drained = \
                        SparseTimeseriesStub(datetime(2012, 1, 9), [0.3, 0.4])
                return summary

        bucket = Mock()

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 10)
        summary = SummedLoadsFromBuckets(start, end, {bucket: BucketOutcome()})
        summary.interesting_labels = ['hardened', 'drained']
        summary.load_summary = StubLoadSummary()

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
        class StubLoadSummary(object):

            def compute(self, bucket, outcome, substance, bound):
                summary = BucketsSummary()
                summary.hardened = \
                    SparseTimeseriesStub(datetime(2012, 1, 9), [0.1, 0.2])
                return summary

        bucket2outcome = {}
        bucket = Mock()
        bucket2outcome[bucket] = BucketOutcome()
        bucket = Mock()
        bucket2outcome[bucket] = BucketOutcome()
        assert 2 == len(bucket2outcome.keys())

        start, end = datetime(2012, 1, 9), datetime(2012, 1, 10)
        summary = SummedLoadsFromBuckets(start, end, bucket2outcome)
        summary.interesting_labels = ['hardened']
        summary.load_summary = StubLoadSummary()

        min_summary, inc_summary = summary.compute_summary('phosphate')

        expected_timeseries = \
            SparseTimeseriesStub(datetime(2012, 1, 9), [0.2, 0.4])

        self.assertEqual(expected_timeseries, min_summary.hardened)


class LoadSummaryTestSuite(TestCase):
    """Implements a test suite for LoadSummary.

    This test suite assumes there is a single bucket with a hardened surface.

    """

    def setUp(self):
        self.today = datetime(2012, 1, 9)
        self.bucket = Mock()
        self.bucket.surface_type = BucketTypes.HARDENED_SURFACE
        self.bucket.min_concentr_phosphate_hardened = 0.2
        self.bucket.incr_concentr_phosphate_hardened = 0.1
        self.bucket.min_concentr_phosphate_drained = 0.3
        self.bucket.incr_concentr_phosphate_drained = 0.4
        self.outcome = BucketOutcome()
        self.outcome.flow_off.add_value(self.today, -10.0)
        self.outcome.net_drainage.add_value(self.today, -20.0)

    def test_a(self):
        """Test the minimum phosphate load of a hardened bucket flow."""
        load_summary = self.create_load_summary()
        load_summary.interesting_labels = ['hardened']
        summary = load_summary.compute(self.bucket, self.outcome, 'phosphate', 'min')
        self.assertEqual(summary.hardened, SparseTimeseriesStub(self.today, [0.2 * 10.0]))

    def create_load_summary(self):
        load_summary = LoadSummary(BucketsSummarizer())
        load_summary.set_time_range(self.today, self.today + timedelta(1))
        return load_summary

    def test_b(self):
        """Test the incremental phosphate load of a hardened bucket flow."""
        load_summary = self.create_load_summary()
        load_summary.interesting_labels = ['hardened']
        summary = load_summary.compute(self.bucket, self.outcome, 'phosphate', 'incr')
        self.assertEqual(summary.hardened, SparseTimeseriesStub(self.today, [0.1 * 10.0]))

    def test_c(self):
        """Test the minimal phosphate load of a drained bucket flow."""
        load_summary = self.create_load_summary()
        load_summary.interesting_labels = ['drained']
        summary = load_summary.compute(self.bucket, self.outcome, 'phosphate', 'min')
        self.assertEqual(summary.drained, SparseTimeseriesStub(self.today, [0.3 * 0.0]))

