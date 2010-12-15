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

from filereader import FileReaderStub
from timeseriesstub import add_timeseries
from timeseriesstub import create_from_file
from timeseriesstub import multiply_timeseries
from timeseriesstub import split_timeseries
from timeseriesstub import TimeseriesStub

class TimeseriesStubTestSuite(TestCase):


    def test_c(self):
        """Test the value on the first date & time is the first value."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        self.assertAlmostEqual(20.0, timeserie.get_value(today))

    def test_d(self):
        """Test the value after the first date & time is the first value."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        tomorrow = today + timedelta(1)
        self.assertAlmostEqual(20.0, timeserie.get_value(tomorrow))

    def test_e(self):
        """Test the value before the second date & time is the first value."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 11, 24)
        timeserie.add_value(today, 20.0)
        tomorrow = today + timedelta(1)
        day_after_tomorrow = tomorrow + timedelta(1)
        timeserie.add_value(day_after_tomorrow, 30.0)
        self.assertAlmostEqual(20.0, timeserie.get_value(tomorrow))

    def test_f(self):
        """Test missing dates are automatically added as zeros."""
        timeserie = TimeseriesStub()
        today = datetime(2010, 12, 3)
        tomorrow = datetime(2010, 12, 4)
        day_after_tomorrow = datetime(2010, 12, 5)
        timeserie.add_value(today, 20)
        timeserie.add_value(day_after_tomorrow, 30)
        events = [event for event in timeserie.events()]

        expected_events = [(today, 20), (tomorrow, 0), (day_after_tomorrow, 30)]
        self.assertEqual(expected_events, events)

    def test_fa(self):
        """Test the aggregation of a single daily events to a monthly event."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        monthly_events = [event for event in timeserie.monthly_events()]
        expected_monthly_events = [(datetime(2010, 12, 1), 20)]
        self.assertEqual(expected_monthly_events, monthly_events)

    def test_fb(self):
        """Test the aggregation of a multiple daily events to a monthly event."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), 30)
        timeserie.add_value(datetime(2010, 12, 10),40)
        monthly_events = [event for event in timeserie.monthly_events()]
        expected_monthly_events = [(datetime(2010, 12, 1), 90)]
        self.assertEqual(expected_monthly_events, monthly_events)

    def test_fc(self):
        """Test the aggregation of a multiple daily events to monthly events."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), 30)
        timeserie.add_value(datetime(2010, 12, 10),40)
        timeserie.add_value(datetime(2011, 1, 1), 50)
        monthly_events = [event for event in timeserie.monthly_events()]
        expected_monthly_events = [(datetime(2010, 12, 1), 90),
                                   (datetime(2011, 1, 1), 50)]
        self.assertEqual(expected_monthly_events, monthly_events)

    def test_g(self):
        """Test add_timeseries on time series with the same start and end date."""
        today = datetime(2010, 12, 5)
        tomorrow = datetime(2010, 12, 6)
        timeserie_a = TimeseriesStub()
        timeserie_a.add_value(today, 10)
        timeserie_a.add_value(tomorrow, 20)
        timeserie_b = TimeseriesStub()
        timeserie_b.add_value(today, 30)
        timeserie_b.add_value(tomorrow, 40)
        expected_timeserie = [(today, 40), (tomorrow, 60)]
        summed_timeseries = list(add_timeseries(timeserie_a, timeserie_b).events())
        self.assertEqual(expected_timeserie, summed_timeseries)

    def test_h(self):
        """Test multiply_timeseries on time series."""
        today = datetime(2010, 12, 5)
        tomorrow = datetime(2010, 12, 6)
        timeserie = TimeseriesStub()
        timeserie.add_value(today, 10)
        timeserie.add_value(tomorrow, 20)
        expected_timeserie = [(today, 40), (tomorrow, 80)]
        multiplied_timeseries = list(multiply_timeseries(timeserie, 4).events())
        self.assertEqual(expected_timeserie, multiplied_timeseries)

    def test_i(self):
        """Test split_timeseries on time series."""
        timeserie = TimeseriesStub()
        timeserie.add_value(datetime(2010, 12, 7), 10)
        timeserie.add_value(datetime(2010, 12, 8), 20)
        timeserie.add_value(datetime(2010, 12, 9), -5)
        expected_negative_timeserie_events = [(datetime(2010, 12, 7), 0),
                                              (datetime(2010, 12, 8), 0),
                                              (datetime(2010, 12, 9), -5)]
        expected_positive_timeserie_events = [(datetime(2010, 12, 7), 10),
                                              (datetime(2010, 12, 8), 20),
                                              (datetime(2010, 12, 9), 0)]
        splitted_timeseries = split_timeseries(timeserie)
        self.assertEqual(expected_negative_timeserie_events, list(splitted_timeseries[0].events()))
        self.assertEqual(expected_positive_timeserie_events, list(splitted_timeseries[1].events()))

class create_from_fileTestSuite(TestCase):

    def test_a(self):
        filereader = FileReaderStub(["openwater,neerslag,1996,1,2,0.000000"])
        result = create_from_file("dont care", filereader)
        expected_timeserie = TimeseriesStub()
        expected_timeserie.add_value(datetime(1996, 1, 2), 0.0)
        expected_result = {}
        expected_result["openwater"] = {}
        expected_result["openwater"]["neerslag"] = expected_timeserie
        self.assertEqual(expected_result, result)

    def test_b(self):
        filereader = FileReaderStub(["openwater,neerslag,1996,1,2,0.000000",
                                     "landelijk,berging,1996,1,2,413025.340000"])
        result = create_from_file("dont care", filereader)
        expected_result = {}
        expected_result["openwater"] = {}
        expected_timeserie = TimeseriesStub()
        expected_timeserie.add_value(datetime(1996, 1, 2), 0.0)
        expected_result["openwater"]["neerslag"] = expected_timeserie
        expected_result["landelijk"] = {}
        expected_timeserie = TimeseriesStub()
        expected_timeserie.add_value(datetime(1996, 1, 2), 413025.34)
        expected_result["landelijk"]["berging"] = expected_timeserie
        self.assertEqual(expected_result, result)
