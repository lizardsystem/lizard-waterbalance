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

from unittest import TestCase

from check_fractions_tests import MockTimeSeries
from check_fractions_tests import create_time_series
from check_symmetry import SummedTimeSeriesReader

class SummedTimeSeriesReader_get_TestSuite(TestCase):

    def test_a(self):
        """Test the sum of a single time series."""
        time_series = MockTimeSeries(
            ('3201', 'discharge_flow_off', 1.0, 0.50, 0.75))
        fractions_reader = SummedTimeSeriesReader(time_series.as_dict)
        time_series = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(create_time_series(1.0, 0.50, 0.75), time_series)

    def test_b(self):
        """Test the sum of two time series."""
        time_series = MockTimeSeries(
            ('3201', 'discharge_flow_off',  1.0,  0.50,  0.75),
            ('3201', 'discharge_hardened', -1.0, -0.50, -0.75))
        fractions_reader = SummedTimeSeriesReader(time_series.as_dict)
        time_series = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(create_time_series(0.0, 0.0, 0.0), time_series)

