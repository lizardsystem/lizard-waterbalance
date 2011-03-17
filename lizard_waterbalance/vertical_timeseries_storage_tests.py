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

from lizard_waterbalance.models import OpenWater
from timeseries.timeseriesstub import TimeseriesStub
from lizard_waterbalance.vertical_timeseries_storage import VerticalTimeseriesStorage

# class VerticalTimeseriesStorageTests(TestCase):

#     def test_a(self):
#         """Test the case that the vertical time series are empty."""
#         vertical_timeseries = [TimeseriesStub(),
#                                TimeseriesStub(),
#                                TimeseriesStub(),
#                                TimeseriesStub()]
#         open_water = OpenWater()
#         open_water.surface = 100
#         open_water.crop_evaporation_factor = 1.0
#         open_water.init_water_level = 1.0
#         open_water.save()
#         storage = VerticalTimeseriesStorage()
#         storage.store(vertical_timeseries, open_water)

#         # we retrieve the open water from the database
#         pk = open_water.pk
#         open_water = OpenWater.objects.get(pk=pk)

#         self.assertEqual([], list(open_water.computed_precipitation.volume.events()))
#         self.assertEqual([], list(open_water.computed_evaporation.volume.events()))
#         self.assertEqual([], list(open_water.computed_seepage.volume.events()))
#         self.assertEqual([], list(open_water.computed_infiltration.volume.events()))

#     def test_b(self):
#         """Test the case that the vertical time series are non-empty."""
#         today = datetime(2011, 1, 29)
#         vertical_timeseries = [TimeseriesStub((today, 4.0)),
#                                TimeseriesStub((today, 2.0)),
#                                TimeseriesStub((today, 1.0)),
#                                TimeseriesStub((today, -1.0))]
#         open_water = OpenWater()
#         open_water.surface = 100
#         open_water.crop_evaporation_factor = 1.0
#         open_water.init_water_level = 1.0
#         open_water.save()
#         storage = VerticalTimeseriesStorage()
#         storage.store(vertical_timeseries, open_water)

#         # we retrieve the open water from the database
#         pk = open_water.pk
#         open_water = OpenWater.objects.get(pk=pk)

#         self.assertEqual(list(vertical_timeseries[0].events()),
#                          list(open_water.computed_precipitation.volume.events()))
#         self.assertEqual(list(vertical_timeseries[1].events()),
#                          list(open_water.computed_evaporation.volume.events()))
#         self.assertEqual(list(vertical_timeseries[2].events()),
#                          list(open_water.computed_seepage.volume.events()))
#         self.assertEqual(list(vertical_timeseries[3].events()),
#                          list(open_water.computed_infiltration.volume.events()))
