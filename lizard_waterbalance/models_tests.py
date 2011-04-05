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

import lizard_fewsunblobbed.models as fews_models

from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import TimeseriesEvent
from lizard_waterbalance.models import TimeseriesFews

class TimeseriesAndTimeseriesFewsTests(TestCase):

    def test_a(self):
        """Test a Timeseries can be saved to the database."""

        timeseries = Timeseries()
        timeseries.save()

        event = TimeseriesEvent()
        event.time = datetime(2011, 4, 4)
        event.value = 10.0
        event.timeseries = timeseries
        event.save()

        event = TimeseriesEvent()
        event.time = datetime(2011, 4, 5)
        event.value = 20.0
        event.timeseries = timeseries
        event.save()

        expected_events = [(datetime(2011, 4, 4), 10.0),
                           (datetime(2011, 4, 5), 20.0)]

        self.assertEqual(expected_events, list(timeseries.events()))

    def test_b(self):
        """Test a sticky Timeseries fills in defaults before the first event.

        """

        timeseries = Timeseries()
        timeseries.default_value = 5.0
        timeseries.stick_to_last_value = True
        timeseries.save()

        for day in range(5, 10):
            event = TimeseriesEvent()
            event.time = datetime(2011, 4, day)
            event.value = 10.0
            event.timeseries = timeseries
            event.save()

        events = timeseries.events(datetime(2011, 4, 1), datetime(2011, 4, 6))

        expected_events = [(datetime(2011, 4, 1), 5.0),
                           (datetime(2011, 4, 2), 5.0),
                           (datetime(2011, 4, 3), 5.0),
                           (datetime(2011, 4, 4), 5.0),
                           (datetime(2011, 4, 5), 10.0),
                           (datetime(2011, 4, 6), 10.0)]

        self.assertEqual(expected_events, list(events))

    def test_c(self):
        """Test a sticky Timeseries fills in defaults after the last event.

        """

        timeseries = Timeseries()
        timeseries.default_value = 5.0
        timeseries.stick_to_last_value = True
        timeseries.save()

        for day in range(5, 10):
            event = TimeseriesEvent()
            event.time = datetime(2011, 4, day)
            event.value = 10.0
            event.timeseries = timeseries
            event.save()

        events = timeseries.events(datetime(2011, 4, 8), datetime(2011, 4, 12))

        expected_events = [(datetime(2011, 4, 8), 10.0),
                           (datetime(2011, 4, 9), 10.0),
                           (datetime(2011, 4, 10), 5.0),
                           (datetime(2011, 4, 11), 5.0),
                           (datetime(2011, 4, 12), 5.0)]

        self.assertEqual(expected_events, list(events))

    def test_d(self):
        """Test a non-sticky Timeseries only returns available events.

        """

        timeseries = Timeseries()
        timeseries.save()

        for day in range(5, 10):
            event = TimeseriesEvent()
            event.time = datetime(2011, 4, day)
            event.value = 10.0
            event.timeseries = timeseries
            event.save()

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

        timeseries = Timeseries()
        timeseries.default_value = 5.0
        timeseries.stick_to_last_value = True
        timeseries.save()

        for day in range(5, 10):
            event = TimeseriesEvent()
            event.time = datetime(2011, 4, day)
            event.value = 10.0
            event.timeseries = timeseries
            event.save()

        events = timeseries.events()

        expected_events = [(datetime(2011, 4, 5), 10.0),
                           (datetime(2011, 4, 6), 10.0),
                           (datetime(2011, 4, 7), 10.0),
                           (datetime(2011, 4, 8), 10.0),
                           (datetime(2011, 4, 9), 10.0)]

        self.assertEqual(expected_events, list(events))
