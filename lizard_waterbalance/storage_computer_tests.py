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
# Initial date:       2011-01-25
#
#******************************************************************************

from datetime import datetime
from unittest import TestCase

from lizard_waterbalance.compute import BucketsSummary
from lizard_waterbalance.storage_computer import StorageComputer
from lizard_waterbalance.timeseriesstub import TimeseriesStub

class StorageComputerTests(TestCase):

    def test_a(self):
        today = datetime(2011, 1, 25)
        surface = 100
        init_water_level = 1.0
        buckets_summary = BucketsSummary()
        intakes_timeseries = []
        pumps_timeseries = []
        precipitation = TimeseriesStub((today, 8))
        evaporation = TimeseriesStub((today, 4))
        seepage = TimeseriesStub((today, 2))
        storage_computer = StorageComputer()
        storage_timeseries = storage_computer.compute(surface,
                                                      init_water_level,
                                                      buckets_summary,
                                                      intakes_timeseries,
                                                      pumps_timeseries,
                                                      precipitation,
                                                      evaporation,
                                                      seepage)
        expected_storage = surface * (init_water_level + 0.008 - 0.004 + 0.002)
        expected_storage_timeseries = TimeseriesStub((today, expected_storage))
        self.assertEqual(expected_storage_timeseries, storage_timeseries)

    def test_b(self):
        today = datetime(2011, 1, 25)
        surface = 100
        init_water_level = 1.0
        buckets_summary = BucketsSummary()
        intakes_timeseries = [TimeseriesStub((today, 10))]
        pumps_timeseries = []
        precipitation = TimeseriesStub((today, 8))
        evaporation = TimeseriesStub((today, 4))
        seepage = TimeseriesStub((today, 2))
        storage_computer = StorageComputer()
        storage_timeseries = storage_computer.compute(surface,
                                                      init_water_level,
                                                      buckets_summary,
                                                      intakes_timeseries,
                                                      pumps_timeseries,
                                                      precipitation,
                                                      evaporation,
                                                      seepage)
        expected_storage = surface * (init_water_level + 0.008 - 0.004 + 0.002) + 10
        expected_storage_timeseries = TimeseriesStub((today, expected_storage))
        self.assertEqual(expected_storage_timeseries, storage_timeseries)

    def test_c(self):
        today = datetime(2011, 1, 25)
        surface = 100
        init_water_level = 1.0
        buckets_summary = BucketsSummary()
        intakes_timeseries = [TimeseriesStub((today, 10))]
        pumps_timeseries = [TimeseriesStub((today, 5))]
        precipitation = TimeseriesStub((today, 8))
        evaporation = TimeseriesStub((today, 4))
        seepage = TimeseriesStub((today, 2))
        storage_computer = StorageComputer()
        storage_timeseries = storage_computer.compute(surface,
                                                      init_water_level,
                                                      buckets_summary,
                                                      intakes_timeseries,
                                                      pumps_timeseries,
                                                      precipitation,
                                                      evaporation,
                                                      seepage)
        expected_storage = surface * (init_water_level + 0.008 - 0.004 + 0.002) + 10 - 5
        expected_storage_timeseries = TimeseriesStub((today, expected_storage))
        self.assertEqual(expected_storage_timeseries, storage_timeseries)

    def test_d(self):
        today = datetime(2011, 1, 25)
        surface = 100
        init_water_level = 1.0
        buckets_summary = BucketsSummary()
        buckets_summary.hardened = TimeseriesStub((today, 3))
        buckets_summary.drained  = TimeseriesStub((today, 6))
        buckets_summary.undrained = TimeseriesStub((today, 9))
        buckets_summary.flow_off = TimeseriesStub((today, 12))
        buckets_summary.infiltration = TimeseriesStub((today, -3))
        intakes_timeseries = [TimeseriesStub((today, 10))]
        pumps_timeseries = [TimeseriesStub((today, 5))]
        precipitation = TimeseriesStub((today, 8))
        evaporation = TimeseriesStub((today, 4))
        seepage = TimeseriesStub((today, 2))
        storage_computer = StorageComputer()
        storage_timeseries = storage_computer.compute(surface,
                                                      init_water_level,
                                                      buckets_summary,
                                                      intakes_timeseries,
                                                      pumps_timeseries,
                                                      precipitation,
                                                      evaporation,
                                                      seepage)
        expected_storage = surface * (init_water_level + 0.008 - 0.004 + 0.002) + 3 + 6  + 9 + 12 - 3 + 10 - 5
        expected_storage_timeseries = TimeseriesStub((today, expected_storage))
        self.assertEqual(list(expected_storage_timeseries.events()), list(storage_timeseries.events()))




