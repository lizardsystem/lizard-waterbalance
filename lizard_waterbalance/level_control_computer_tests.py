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
from datetime import timedelta
from unittest import TestCase

from lizard_waterbalance.compute import BucketsSummary
from lizard_waterbalance.level_control_computer import LevelControlComputer
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.timeseriesstub import TimeseriesWithMemoryStub
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class LevelControlComputerTests(TestCase):
    """Contains tests for the level control computation of an open water.

    The tests in this suite verify that LevelControlComputer computes the right
    sluice error.

    """

    def setUp(self):
        """Create the fixture for the tests in this suite."""
        self.open_water = OpenWater()
        self.open_water.surface = 100
        self.open_water.init_water_level = 1.0
        self.open_water.crop_evaporation_factor = 1.0
        self.today = datetime(2010, 12, 17)
        water_levels = TimeseriesWithMemoryStub((self.today, 1.0))
        self.open_water.retrieve_minimum_level = lambda : water_levels
        self.open_water.retrieve_maximum_level = lambda : water_levels
        self.buckets_summary = BucketsSummary()

    def test_a(self):
        """Test the case with precipitation on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = []
        pumps_timeseries = []
        precipitation = TimeseriesStub((self.today, 2.0))
        evaporation = TimeseriesStub((self.today, 0.0))
        seepage = TimeseriesStub((self.today, 0.0))
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -0.2)))
        self.assertEqual(expected_timeseries, timeseries)

    def test_b(self):
        """Test the case with precipitation on two days."""
        level_control = LevelControlComputer()
        tomorrow = self.today + timedelta(1)
        intakes_timeseries = []
        pumps_timeseries = []
        precipitation = TimeseriesStub((self.today, 2.0), (tomorrow, 1.0))
        evaporation = TimeseriesStub((self.today, 0.0), (tomorrow, 0.0))
        seepage = TimeseriesStub((self.today, 0.0), (tomorrow, 0.0))
        water_levels = TimeseriesWithMemoryStub((self.today, 1.0),
                                                (tomorrow, 1.0))
        self.open_water.retrieve_minimum_level = lambda : water_levels
        self.open_water.retrieve_maximum_level = lambda : water_levels
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, -0.2), (tomorrow, -0.1)))
        self.assertEqual(expected_timeseries, timeseries)

    def test_c(self):
        """Test the case with precipitation and evaporation on a single day."""
        level_control = LevelControlComputer()
        precipitation = TimeseriesStub((self.today, 2.0))
        intakes_timeseries = []
        pumps_timeseries = []
        evaporation = TimeseriesStub((self.today, 1.0))
        seepage = TimeseriesStub((self.today, 0.0))
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -0.1)))
        self.assertEqual(expected_timeseries, timeseries)

    def test_d(self):
        """Test the case with precipitation, evaporation and seepage on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = []
        pumps_timeseries = []
        precipitation = TimeseriesStub((self.today, 2.0))
        evaporation = TimeseriesStub((self.today, 1.0))
        seepage = TimeseriesStub((self.today, 0.5))
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -0.1500)))
        self.assertEqual(expected_timeseries, timeseries)

    def test_e(self):
        """Test the case with evaporation on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = []
        pumps_timeseries = []
        precipitation = TimeseriesStub((self.today, 0.0))
        evaporation = TimeseriesStub((self.today, 1.0))
        seepage = TimeseriesStub((self.today, 0.0))
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 0.1)),
                               TimeseriesStub((self.today, 0.0)))
        self.assertEqual(expected_timeseries, timeseries)

    def test_f(self):
        """Test the case with a single intake time series."""
        level_control = LevelControlComputer()
        buckets_summary = BucketsSummary()
        intakes_timeseries = [TimeseriesStub((self.today, 10))]
        pumps_timeseries = []
        precipitation = TimeseriesStub((self.today, 8.0))
        evaporation = TimeseriesStub((self.today, 4.0))
        seepage = TimeseriesStub((self.today, 2.0))
        timeseries = level_control.compute(self.open_water,
                                           buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -10.6)))
        self.assertEqual(expected_timeseries[0], timeseries[0])
        self.assertEqual(expected_timeseries[1], timeseries[1])

    def test_g(self):
        """Test the case with a single pump time series."""
        level_control = LevelControlComputer()
        buckets_summary = BucketsSummary()
        intakes_timeseries = []
        pumps_timeseries = [TimeseriesStub((self.today, 10))]
        precipitation = TimeseriesStub((self.today, 8.0))
        evaporation = TimeseriesStub((self.today, 4.0))
        seepage = TimeseriesStub((self.today, 2.0))
        timeseries = level_control.compute(self.open_water,
                                           buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 9.4)),
                               TimeseriesStub((self.today, 0.0)))
        self.assertEqual(expected_timeseries[0], timeseries[0])
        self.assertEqual(expected_timeseries[1], timeseries[1])

    def test_h(self):
        """Test the case with multiple pump time series."""
        level_control = LevelControlComputer()
        buckets_summary = BucketsSummary()
        intakes_timeseries = []
        pumps_timeseries = [TimeseriesStub((self.today, 10)), TimeseriesStub((self.today, 10))]
        precipitation = TimeseriesStub((self.today, 8.0))
        evaporation = TimeseriesStub((self.today, 4.0))
        seepage = TimeseriesStub((self.today, 2.0))
        timeseries = level_control.compute(self.open_water,
                                           buckets_summary,
                                           intakes_timeseries,
                                           pumps_timeseries,
                                           precipitation,
                                           evaporation,
                                           seepage)
        expected_timeseries = (TimeseriesStub((self.today, 19.4)),
                               TimeseriesStub((self.today, 0.0)))
        self.assertEqual(expected_timeseries[0], timeseries[0])
        self.assertEqual(expected_timeseries[1], timeseries[1])
