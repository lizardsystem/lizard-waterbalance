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
        substance = 'nitrogen'
        buckets2daily_outcome = impact.compute(start, end, substance)
        self.assertEqual({}, buckets2daily_outcome)

    def test_b(self):
        """Test the correct dict is returned when a single bucket is present."""

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 3)

        bucket = Mock()
        bucket.min_concentr_nitrogen_flow_off = 2.0

        daily_outcome = BucketOutcome()
        daily_outcome.flow_off.add_value(start, 10.0)

        impact = ImpactFromBuckets({bucket: daily_outcome})

        substance = 'nitrogen'
        bucket2impact = impact.compute(start, end, substance)

        self.assertEqual([bucket], bucket2impact.keys())

        flow_off_events = list(bucket2impact[bucket].flow_off.events())
        self.assertEqual(1, len(flow_off_events))
        self.assertEqual((start, 20.0), flow_off_events[0])


class SummedImpactFromBucketsTestSuite(TestCase):

    def test_a(self):
        """Test the time series are returned that match the computed BucketsSummary."""
        area = Mock()
        area.location_id = 20120102

        impact = SummedImpactFromBuckets(area)

        impact.compute_buckets_timeseries = lambda start, end: {}
        impact.compute_buckets_summary = BucketsSummarizer().compute

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 4)
        substance = 'nitrogen'
        min_timeseries, incr_timeseries = impact.compute(start, end, substance)

        self.assertEqual(5, len(min_timeseries))
        self.assertEqual('min_impact_nitrogen_hardened', min_timeseries[0].parameter_id)
        self.assertEqual('min_impact_nitrogen_drained', min_timeseries[1].parameter_id)
        self.assertEqual('min_impact_nitrogen_flow_off', min_timeseries[2].parameter_id)
        self.assertEqual('min_impact_nitrogen_drainage', min_timeseries[3].parameter_id)
        self.assertEqual('min_impact_nitrogen_sewer', min_timeseries[4].parameter_id)

        self.assertEqual([], list(min_timeseries[0].events()))

        self.assertEqual(5, len(incr_timeseries))
        self.assertEqual('incr_impact_nitrogen_hardened', incr_timeseries[0].parameter_id)
        self.assertEqual('incr_impact_nitrogen_drained', incr_timeseries[1].parameter_id)
        self.assertEqual('incr_impact_nitrogen_flow_off', incr_timeseries[2].parameter_id)
        self.assertEqual('incr_impact_nitrogen_drainage', incr_timeseries[3].parameter_id)
        self.assertEqual('incr_impact_nitrogen_sewer', incr_timeseries[4].parameter_id)
