#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
# Initial date:       2010-11-24
#
#******************************************************************************


from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from timeseriesstub import TimeseriesStub

class TimeseriesStubTestSuite(TestCase):

    def test_a(self):
        """Test the initial value is set correctly."""
        timeserie = TimeseriesStub(initial_value=10.0)
        today = datetime(2010, 11, 24)
        self.assertAlmostEqual(10.0, timeserie.get_value(today))

    def test_b(self):
        """Test the value before the first date & time is the initial value."""
        timeserie = TimeseriesStub(initial_value=10.0)
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        yesterday = today + timedelta(-1)
        self.assertAlmostEqual(10.0, timeserie.get_value(yesterday))

    def test_c(self):
        """Test the value on the first date & time is the first value."""
        timeserie = TimeseriesStub(initial_value=10.0)
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        self.assertAlmostEqual(20.0, timeserie.get_value(today))

    def test_d(self):
        """Test the value after the first date & time is the first value."""
        timeserie = TimeseriesStub(initial_value=10.0)
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        tomorrow = today + timedelta(1)
        self.assertAlmostEqual(20.0, timeserie.get_value(tomorrow))

    def test_e(self):
        """Test the value before the second date & time is the first value."""
        timeserie = TimeseriesStub(initial_value=10.0)
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        tomorrow = today + timedelta(1)
        day_after_tomorrow = tomorrow + timedelta(1)
        timeserie.add_value(day_after_tomorrow, 30.0)
        self.assertAlmostEqual(20.0, timeserie.get_value(tomorrow))

    def test_f(self):
        """Test missing dates are automatically added."""
        timeserie = TimeseriesStub(0)
        today = datetime(2010, 12, 3)
        tomorrow = datetime(2010, 12, 4)
        day_after_tomorrow = datetime(2010, 12, 5)
        timeserie.add_value(today, 20)
        timeserie.add_value(day_after_tomorrow, 30)
        events = [event for event in timeserie.events()]

        expected_events = [(today, 20), (tomorrow, 20), (day_after_tomorrow, 30)]
        self.assertEqual(expected_events, events)
