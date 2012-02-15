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

from timeseries.timeseries import TimeSeries

from check_fractions import SummedFractionsReader
from check_fractions import Fractions


def create_time_series(*args):
    time_series = TimeSeries()
    for index, value in enumerate(args):
        time_series[datetime(2012, 2,  9 + index, 23, 0)] = value
    return time_series


class MockFractionsReader(object):

    def __init__(self, *args):
        self.get = Mock(return_value=create_time_series(*args))


class Fractions_verify_TestSuite(TestCase):

    def test_a(self):
        """Test for a single fraction time series whose values are always 1."""
        fractions = Fractions(MockFractionsReader(1.0, 1.0, 1.0))
        self.assertTrue(fractions.verify('waterbalance-graph.xml'))

    def test_b(self):
        """Test for a single fraction time series whose values are not always 1.

        """
        fractions = Fractions(MockFractionsReader(1.0, 0.8, 1.0))
        self.assertFalse(fractions.verify('waterbalance-graph.xml'))


class MockTimeSeries(object):

    def __init__(self, *args):
        self.input = {}
        for time_series_spec in args:
            location, parameter = time_series_spec[0:2]
            values = time_series_spec[2:]
            self.input[(location, parameter)] = create_time_series(*values)

    def as_dict(self, file_name):
        return self.input


class SummedFractionsReader_get_TestSuite(TestCase):

    def test_a(self):
        """Test the sum of a single time series."""
        time_series = MockTimeSeries(
            ('3201', 'fraction_water_undrained', 1.0, 0.50, 0.75))
        fractions_reader = SummedFractionsReader(time_series.as_dict)
        time_series = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(create_time_series(1.0, 0.50, 0.75), time_series)

    def test_b(self):
        """Test the sum of two time series."""
        time_series = MockTimeSeries(
            ('3201',     'fraction_water_undrained', 1.0, 0.50, 0.75),
            ('3201_PS1', 'fraction_water_discharge', 0.0, 0.25, 0.10))
        fractions_reader = SummedFractionsReader(time_series.as_dict)
        time_series = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(create_time_series(1.0, 0.75, 0.85), time_series)

    def test_c(self):
        """Test the sum of three time series.

        One of the time series is not a fraction time series.

        """
        time_series = MockTimeSeries(
            ('3201',     'fraction_water_undrained',       1.0, 0.50, 0.75),
            ('3201_PS1', 'fraction_water_discharge',       0.0, 0.25, 0.10),
            ('3201_PS1', 'min_impact_phosphate_discharge', 0.2, 0.20, 0.20))
        fractions_reader = SummedFractionsReader(time_series.as_dict)
        time_series = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(create_time_series(1.0, 0.75, 0.85), time_series)
