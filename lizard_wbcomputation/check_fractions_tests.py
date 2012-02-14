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


class MockFractionsReader(object):

    def __init__(self, *args):
        fraction_timeseries = TimeSeries()
        for index, value in enumerate(args):
            fraction_timeseries[datetime(2012, 2,  9 + index, 23, 0)] = value
        self.get = Mock(return_value=fraction_timeseries)


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


class SummedFractionsReader_get_TestSuite(TestCase):

    def test_a(self):
        """Test the sum of a single time series."""
        fractions_reader = SummedFractionsReader()

        fractions_reader.fraction_timeseries_list = []
        fractions_reader.fraction_timeseries_list.append(MockFractionsReader(1.0, 0.5, 0.75).get())

        expected_fraction_timeseries = MockFractionsReader(1.0, 0.5, 0.75).get()

        fraction_timeseries = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(expected_fraction_timeseries, fraction_timeseries)

    def test_b(self):
        """Test the sum of two time series."""
        fractions_reader = SummedFractionsReader()

        fractions_reader.fraction_timeseries_list = []
        fractions_reader.fraction_timeseries_list.append(MockFractionsReader(1.0, 0.50, 0.75).get())
        fractions_reader.fraction_timeseries_list.append(MockFractionsReader(0.0, 0.25, 0.10).get())

        expected_fraction_timeseries = MockFractionsReader(1.0, 0.75, 0.85).get()

        fraction_timeseries = fractions_reader.get('waterbalance-graph.xml')
        self.assertEqual(expected_fraction_timeseries, fraction_timeseries)


