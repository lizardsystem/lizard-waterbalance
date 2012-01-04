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

from lizard_wbcomputation.bucket_computer import BucketOutcome
from lizard_wbcomputation.bucket_summarizer import BucketsSummarizer
from lizard_wbcomputation.impact_from_buckets import ImpactFromBuckets
from lizard_wbcomputation.impact_from_buckets import SummedImpactFromBuckets


class ImpactFromBucketsTestSuite(TestCase):

    def test_a(self):
        """Test the empty dict is returned when no buckets are present."""
        bucket2outcome = {}
        impact = ImpactFromBuckets(bucket2outcome)

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        type = 'min'
        substance = 'nitrogen'
        buckets2daily_outcome = impact.compute(start, end, type, substance)
        self.assertEqual({}, buckets2daily_outcome)

    def test_b(self):
        """Test the correct dict is returned when a single event is present.

        There exists a single bucket."""

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 3)

        bucket = Mock()
        bucket.min_concentr_nitrogen_flow_off = 2.0

        daily_outcome = BucketOutcome()
        daily_outcome.flow_off.add_value(start, 10.0)

        impact = ImpactFromBuckets({bucket: daily_outcome})

        type = 'min'
        substance = 'nitrogen'
        bucket2impact = impact.compute(start, end, substance, type)

        self.assertEqual([bucket], bucket2impact.keys())

        events = list(bucket2impact[bucket].flow_off.events())
        self.assertEqual([(start, 20.0)], events)

    def test_c(self):
        """Test the correct dict is returned when two events are present.

        There exists a single bucket."""

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)

        bucket = Mock()
        bucket.min_concentr_nitrogen_flow_off = 2.0

        daily_outcome = BucketOutcome()
        daily_outcome.flow_off.add_value(start, 10.0)
        daily_outcome.flow_off.add_value(start + timedelta(1), 20.0)

        impact = ImpactFromBuckets({bucket: daily_outcome})

        type = 'min'
        substance = 'nitrogen'
        bucket2impact = impact.compute(start, end, substance, type)

        self.assertEqual([bucket], bucket2impact.keys())

        events = list(bucket2impact[bucket].flow_off.events())
        self.assertEqual([(start, 20.0), (start + timedelta(1), 40.0)], events)

    def test_d(self):
        """Test the correct dict is returned when two events are present.

        There exists a single bucket."""

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)

        bucket = Mock()
        bucket.incr_concentr_nitrogen_flow_off = 2.0

        daily_outcome = BucketOutcome()
        daily_outcome.flow_off.add_value(start, 10.0)
        daily_outcome.flow_off.add_value(start + timedelta(1), 20.0)

        impact = ImpactFromBuckets({bucket: daily_outcome})

        type = 'incr'
        substance = 'nitrogen'
        bucket2impact = impact.compute(start, end, substance, type)

        self.assertEqual([bucket], bucket2impact.keys())

        events = list(bucket2impact[bucket].flow_off.events())
        self.assertEqual([(start, 20.0), (start + timedelta(1), 40.0)], events)


class SummedImpactFromBucketsTestSuite(TestCase):

    def test_a(self):
        """Test the correct load is returned when no bucket is present."""
        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        impact = SummedImpactFromBuckets(start, end)

        impact.compute_bucket2load_timeseries = lambda start, end, substance, type: {}
        impact.compute_buckets_summary = BucketsSummarizer().compute

        substance = 'nitrogen'
        min_loads, incr_loads = impact.compute(substance)

        expected_labels = ['flow_off']
        labels = [load.label for load in min_loads]
        self.assertEqual(set(expected_labels), set(labels))

        expected_labels = ['flow_off']
        labels = [load.label for load in incr_loads]
        self.assertEqual(set(expected_labels), set(labels))

    def test_b(self):
        """Test the correct load is returned when events are present."""
        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        impact = SummedImpactFromBuckets(start, end)

        daily_outcome = BucketOutcome()
        daily_outcome.flow_off.add_value(start, 20.0)
        daily_outcome.flow_off.add_value(start + timedelta(1), 40.0)

        impact.compute_bucket2load_timeseries = lambda start, end, substance, type: {}
        impact.compute_buckets_summary = lambda bucket2outcome, start, end: daily_outcome

        substance = 'nitrogen'
        min_loads, incr_loads = impact.compute(substance)

        self.assertEqual(daily_outcome.flow_off, min_loads[0].timeseries)
        self.assertEqual(daily_outcome.flow_off, incr_loads[0].timeseries)
