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

from lizard_waterbalance.bucket_summarizer import BucketsSummary
from lizard_waterbalance.level_control_computer import LevelControlComputer
from lizard_waterbalance.models import OpenWater
from timeseries.timeseriesstub import TimeseriesWithMemoryStub
from timeseries.timeseriesstub import TimeseriesStub


class LevelControlComputerTests(TestCase):
    """Contains tests for the level control computation of an open water."""

    def setUp(self):
        """Create the fixture for the tests in this suite."""
        self.open_water = OpenWater()
        self.open_water.surface = 100
        self.open_water.init_water_level = 1.0
        self.open_water.crop_evaporation_factor = 1.0
        self.open_water.bottom_height = 0.9
        self.today = datetime(2010, 12, 17)
        self.water_levels = TimeseriesWithMemoryStub((self.today, 1.0))
        self.buckets_summary = BucketsSummary()

    def test_a(self):
        """Test the case with precipitation on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],                                          
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -2.0)))
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_b(self):
        """Test the case with precipitation on two days."""
        level_control = LevelControlComputer()
        tomorrow = self.today + timedelta(1)
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0), (tomorrow, 1.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0))]
        water_levels = TimeseriesWithMemoryStub((self.today, 1.0),
                                                (tomorrow, 1.0))
        self.open_water.retrieve_minimum_level = lambda : water_levels
        self.open_water.retrieve_maximum_level = lambda : water_levels
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           water_levels,
                                           water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, -2.0), (tomorrow, -1.0)))
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_c(self):
        """Test the case with precipitation and evaporation on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, -1.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -1.0)))
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_d(self):
        """Test the case with precipitation, evaporation and seepage on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, -1.0)),
                               TimeseriesStub((self.today, 0.5)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -1.5)))
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_e(self):
        """Test the case with evaporation on a single day."""
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -1.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 1.0)),
                               TimeseriesStub((self.today, 0.0)))
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_f(self):
        """Test the case with a single intake time series."""
        level_control = LevelControlComputer()
        buckets_summary = BucketsSummary()
        intakes_timeseries = {'a':TimeseriesStub((self.today, 10))}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 8.0)),
                               TimeseriesStub((self.today, -4.0)),
                               TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -16.0)))
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_g(self):
        """Test the case with a single pump time series."""
        level_control = LevelControlComputer()
        buckets_summary = BucketsSummary()
        intakes_timeseries = {}
        pumps_timeseries = {'a':TimeseriesStub((self.today, 10))}
        vertical_timeseries = [TimeseriesStub((self.today, 8.0)),
                               TimeseriesStub((self.today, -4.0)),
                               TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 4.0)),
                               TimeseriesStub((self.today, 0.0)))
        
        print next(timeseries['intake'].events())
        print next(timeseries['pump'].events())
        
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

    def test_h(self):
        """Test the case with multiple pump time series."""
        level_control = LevelControlComputer()
        buckets_summary = BucketsSummary()
        intakes_timeseries = {}
        pumps_timeseries = {'a':TimeseriesStub((self.today, 10)), 'b':TimeseriesStub((self.today, 10))}
        vertical_timeseries = [TimeseriesStub((self.today, 8.0)),
                               TimeseriesStub((self.today, -4.0)),
                               TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.water_levels,
                                           self.water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = (TimeseriesStub((self.today, 14.0)),
                               TimeseriesStub((self.today, 0.0)))
        print next(timeseries['intake'].events())
        print next(timeseries['pump'].events())
        self.assertEqual(expected_timeseries[0], timeseries['intake'])
        self.assertEqual(expected_timeseries[1], timeseries['pump'])

class StorageTests(TestCase):
    """Contains tests for the storage computation by a LevelControlComputer."""

    def setUp(self):
        """Create the fixture for the tests in this suite."""
        self.open_water = OpenWater()
        self.open_water.surface = 100
        self.open_water.init_water_level = 1.0
        self.open_water.crop_evaporation_factor = 1.0
        self.open_water.bottom_height = 0.9
        self.today = datetime(2010, 12, 17)
        self.minimum_water_levels = TimeseriesWithMemoryStub((self.today, 0.98))
        self.maximum_water_levels = TimeseriesWithMemoryStub((self.today, 1.02))
        self.buckets_summary = BucketsSummary()

    def test_a(self):
        """Test the case with precipitation on a single day.

        The precipitation does not rise the water level above the maximum.

        """
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.minimum_water_levels,
                                           self.maximum_water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = TimeseriesStub((self.today, 12.0))
        self.assertEqual(expected_timeseries, timeseries['storage'])

    def test_b(self):
        """Test the case with precipitation on a single day.

        The precipitation does rise the water level above the maximum.

        """
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 4.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.minimum_water_levels,
                                           self.maximum_water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = TimeseriesStub((self.today, 12.0))
        self.assertEqual(expected_timeseries, timeseries['storage'])

    def test_c(self):
        """Test the case with evaporation on a single day.

        The precipitation does reduce the water level below the minimum.

        """
        level_control = LevelControlComputer()
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, -4.0)),
                               TimeseriesStub((self.today, 0.0)),
                               TimeseriesStub((self.today, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           self.minimum_water_levels,
                                           self.maximum_water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = TimeseriesStub((self.today, 8.0))
        self.assertEqual(expected_timeseries, timeseries['storage'])

    def test_d(self):
        """Test the case with precipitation on two days.

        The precipitation does rise the water level above the maximum on the
        second day.

        """
        level_control = LevelControlComputer()
        tomorrow = self.today + timedelta(1)
        minimum_water_levels = TimeseriesWithMemoryStub((self.today, 0.98),
                                                        (tomorrow, 0.98))
        maximum_water_levels = TimeseriesWithMemoryStub((self.today, 1.02),
                                                        (tomorrow, 1.02))
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0), (tomorrow, 2.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           minimum_water_levels,
                                           maximum_water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = TimeseriesStub((self.today, 12.0),
                                             (tomorrow, 12.0))
        self.assertEqual(expected_timeseries, timeseries['storage'])

    def test_e(self):
        """Test the case with both precipitation and evaporation on two days.

        """
        level_control = LevelControlComputer()
        tomorrow = self.today + timedelta(1)
        minimum_water_levels = TimeseriesWithMemoryStub((self.today, 0.98),
                                                        (tomorrow, 0.98))
        maximum_water_levels = TimeseriesWithMemoryStub((self.today, 1.02),
                                                        (tomorrow, 1.02))
        intakes_timeseries = {}
        pumps_timeseries = {}
        vertical_timeseries = [TimeseriesStub((self.today, 2.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, -6.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0)),
                               TimeseriesStub((self.today, 0.0), (tomorrow, 0.0))]
        timeseries = level_control.compute(self.open_water,
                                           self.buckets_summary,
                                           vertical_timeseries[0],
                                           vertical_timeseries[1],  
                                           vertical_timeseries[2], 
                                           vertical_timeseries[3],  
                                           minimum_water_levels,
                                           maximum_water_levels,
                                           intakes_timeseries,
                                           pumps_timeseries)
        expected_timeseries = TimeseriesStub((self.today, 12.0),
                                             (tomorrow, 8.0))
        self.assertEqual(expected_timeseries, timeseries['storage'])
