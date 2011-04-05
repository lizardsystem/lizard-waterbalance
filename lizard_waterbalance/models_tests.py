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
# Copyright 2011 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
#
#******************************************************************************

from datetime import datetime
from unittest import TestCase

from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import TimeseriesEvent


class TimeseriesTests(TestCase):

    def setup_timeseries(self):
        """Return a non-sticky time series in the database."""
        timeseries = Timeseries()
        timeseries.save()
        self.setup_events(timeseries)
        return timeseries

    def setup_sticky_timeseries(self):
        """Return a non-sticky time series in the database."""
        timeseries = Timeseries()
        timeseries.default_value = 5.0
        timeseries.stick_to_last_value = True
        timeseries.save()
        self.setup_events(timeseries)
        return timeseries

    def setup_events(self, timeseries):
        """Create events for the given time series in the database."""
        for day in range(5, 10):
            event = TimeseriesEvent()
            event.time = datetime(2011, 4, day)
            event.value = 10.0
            event.timeseries = timeseries
            event.save()

    def test_a(self):
        """Test a Timeseries can be saved to the database."""

        timeseries = self.setup_timeseries()
        expected_events = [(datetime(2011, 4, 5), 10.0),
                           (datetime(2011, 4, 6), 10.0),
                           (datetime(2011, 4, 7), 10.0),
                           (datetime(2011, 4, 8), 10.0),
                           (datetime(2011, 4, 9), 10.0)]
        self.assertEqual(expected_events, list(timeseries.events()))

    def test_b(self):
        """Test a sticky Timeseries fills in defaults before the first event.

        """
        timeseries = self.setup_sticky_timeseries()
        events = timeseries.events(datetime(2011, 4, 1), datetime(2011, 4, 6))
        expected_events = [(datetime(2011, 4, 1), 5.0),
                           (datetime(2011, 4, 2), 5.0),
                           (datetime(2011, 4, 3), 5.0),
                           (datetime(2011, 4, 4), 5.0),
                           (datetime(2011, 4, 5), 10.0),
                           (datetime(2011, 4, 6), 10.0)]
        self.assertEqual(expected_events, list(events))

    def test_c(self):
        """Test a sticky Timeseries fills in defaults after the last event."""
        timeseries = self.setup_sticky_timeseries()
        events = timeseries.events(datetime(2011, 4, 8), datetime(2011, 4, 12))
        expected_events = [(datetime(2011, 4, 8), 10.0),
                           (datetime(2011, 4, 9), 10.0),
                           (datetime(2011, 4, 10), 5.0),
                           (datetime(2011, 4, 11), 5.0),
                           (datetime(2011, 4, 12), 5.0)]
        self.assertEqual(expected_events, list(events))

    def test_d(self):
        """Test a non-sticky Timeseries only returns available events."""

        timeseries = self.setup_timeseries()
        events = timeseries.events(datetime(2011, 4, 1), datetime(2011, 4, 12))
        expected_events = [(datetime(2011, 4, 5), 10.0),
                           (datetime(2011, 4, 6), 10.0),
                           (datetime(2011, 4, 7), 10.0),
                           (datetime(2011, 4, 8), 10.0),
                           (datetime(2011, 4, 9), 10.0)]
        self.assertEqual(expected_events, list(events))

    def test_e(self):
        """Test a sticky Timeseries only returns available events.

        We will call Timeseries.events without a start or end.

        """
        timeseries = self.setup_sticky_timeseries()
        events = timeseries.events()
        expected_events = [(datetime(2011, 4, 5), 10.0),
                           (datetime(2011, 4, 6), 10.0),
                           (datetime(2011, 4, 7), 10.0),
                           (datetime(2011, 4, 8), 10.0),
                           (datetime(2011, 4, 9), 10.0)]
        self.assertEqual(expected_events, list(events))
