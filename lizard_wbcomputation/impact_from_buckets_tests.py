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

from lizard_wbcomputation.bucket_summarizer import BucketsSummarizer
from lizard_wbcomputation.impact_from_buckets import ImpactFromBuckets

class ImpactFromBucketsTestSuite(TestCase):

    def test_a(self):
        """Test the time series are returned that match the computed BucketsSummary."""
        area = Mock()
        area.location_id = 20120102

        impact = ImpactFromBuckets(area)

        impact.compute_buckets_timeseries = lambda start, end: {}
        impact.compute_buckets_summary = BucketsSummarizer().compute

        start, end = datetime(2012, 1, 2), datetime(2012, 1, 3)
        substance = 'nitrogen'
        min_timeseries, incr_timeseries = impact.compute(start, end, substance)

        self.assertEqual(5, len(min_timeseries))
        self.assertEqual('min_impact_nitrogen_hardened', min_timeseries[0].parameter_id)
        self.assertEqual('min_impact_nitrogen_drained', min_timeseries[1].parameter_id)
        self.assertEqual('min_impact_nitrogen_flow_off', min_timeseries[2].parameter_id)
        self.assertEqual('min_impact_nitrogen_drainage', min_timeseries[3].parameter_id)
        self.assertEqual('min_impact_nitrogen_sewer', min_timeseries[4].parameter_id)

        self.assertEqual(5, len(incr_timeseries))
        self.assertEqual('incr_impact_nitrogen_hardened', incr_timeseries[0].parameter_id)
        self.assertEqual('incr_impact_nitrogen_drained', incr_timeseries[1].parameter_id)
        self.assertEqual('incr_impact_nitrogen_flow_off', incr_timeseries[2].parameter_id)
        self.assertEqual('incr_impact_nitrogen_drainage', incr_timeseries[3].parameter_id)
        self.assertEqual('incr_impact_nitrogen_sewer', incr_timeseries[4].parameter_id)
