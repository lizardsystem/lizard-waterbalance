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
from lizard_wbcomputation.impact_from_buckets import ImpactFromBuckets
from lizard_wbcomputation.impact_from_buckets import SummedLoadsFromBuckets

class ImpactFromBucketsTestSuite(TestCase):

    def test_a(self):
        """Test the empty dict is returned when no buckets are present."""
        bucket_outcomes = {}
        impact = ImpactFromBuckets(bucket_outcomes)

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)

        bucket_loads = impact.compute(start, end, 'nitrogen', 'min')
        self.assertEqual({}, bucket_loads)

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
        impact = SummedLoadsFromBuckets(start, end)
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
        impact = SummedLoadsFromBuckets(start, end)
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
        impact = SummedLoadsFromBuckets(start, end)
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

    # def test_b(self):
    #     """Test the correct load is returned when events are present."""
    #     start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
    #     impact = SummedLoadsFromBuckets(start, end)

    #     buckets_summary = BucketsSummary()
    #     buckets_summary.flow_off.add_value(start, 20.0)
    #     buckets_summary.flow_off.add_value(start + timedelta(1), 40.0)
    #     buckets_summary.hardened.add_value(start, 60.0)
    #     buckets_summary.hardened.add_value(start + timedelta(1), 80.0)

    #     impact.interesting_attributes = ['hardened', 'flow_off']
    #     impact.compute_bucket2load_timeseries = lambda start, end, substance, type: {}
    #     impact.compute_buckets_summary = lambda bucket2outcome, start, end: buckets_summary

    #     substance = 'nitrogen'
    #     min_loads, incr_loads = impact.compute(substance)

    #     expected_timeseries = [buckets_summary.flow_off, buckets_summary.hardened]

    #     min_timeseries = [l.timeseries for l in min_loads]
    #     self.assertEqual(expected_timeseries.sort(), min_timeseries.sort())

    #     incr_timeseries = [l.timeseries for l in incr_loads]
    #     self.assertEqual(expected_timeseries.sort(), incr_timeseries.sort())

