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

from timeseries.timeseriesstub import SparseTimeseriesStub

from lizard_wbcomputation.concentration_computer import ConcentrationComputer
from lizard_wbcomputation.concentration_computer import TotalVolumeChlorideTimeseries


class ConcentrationComputer_compute_TestSuite(TestCase):
    """Implements a test suite for method ConcentrationComputer::compute."""

    def test_a(self):
        """Test that without incoming flows the concentration remains the same.

        There is a single event.

        """
        concentrations = ConcentrationComputer()
        concentrations.initial_concentration = 30.0 # [g/m3]
        concentrations.initial_volume = 100.0

        concentrations.incoming_volumes = self.timeseries(0.0)
        concentrations.incoming_chlorides = self.timeseries(0.0)
        concentrations.outgoing_volumes = self.timeseries(-20.0)

        concentration_timeseries = concentrations.compute()

        self.assertEqual(self.timeseries(30.0), concentration_timeseries)

    def timeseries(self, *args, **kwargs):
        date = datetime(2012, 1, 12)
        return SparseTimeseriesStub(date, list(args))

    def test_b(self):
        """Test that without incoming flows the concentration remains the same.

        There are multiple events.

        """
        concentrations = ConcentrationComputer()
        concentrations.initial_concentration = 30.0 # [g/m3]
        concentrations.initial_volume = 100.0

        concentrations.incoming_volumes = self.timeseries(0.0, 0.0)
        concentrations.incoming_chlorides = self.timeseries(0.0, 0.0)
        concentrations.outgoing_volumes = self.timeseries(-20.0, -30.0)

        concentration_timeseries = concentrations.compute()

        self.assertEqual(self.timeseries(30.0, 30.0), concentration_timeseries)

    def test_c(self):
        """Test the concentration with incoming events.

        There are multiple events.

        """
        concentrations = ConcentrationComputer()
        concentrations.initial_concentration = 30.0 # [g/m3]
        concentrations.initial_volume = 100.0

        concentrations.incoming_volumes = self.timeseries(20.0, 10.0)
        concentrations.incoming_chlorides = self.timeseries(200.0, 250.0)
        concentrations.outgoing_volumes = self.timeseries(-30.0, -10.0)

        concentration_timeseries = concentrations.compute()

        expected_concentrations = [((90.0 / 120.0) * 3200.0) / 90.0]
        expected_concentrations.append(((90.0 / 100.0) * 2650.0) / 90.0)

        self.assertEqual(self.timeseries(*expected_concentrations), concentration_timeseries)


class TotalVolumeChlorideTimeseries_compute_TestSuite(TestCase):

    def test_a(self):
        """Test the incoming volume and chloride levels.

        There is only precipitation incoming.

        """
        date = datetime(2012, 1, 18)

        precipitation = SparseTimeseriesStub(date, [10.0, 20.0])
        seepage = SparseTimeseriesStub()
        volumes = [precipitation, seepage]

        precipitation_chloride = 2.0
        seepage_chloride = 6.0
        concentrations = [precipitation_chloride, seepage_chloride]

        incoming = TotalVolumeChlorideTimeseries(volumes, concentrations)
        volume_timeseries, chloride_timeseries = incoming.compute()

        self.assertEqual(SparseTimeseriesStub(date, [10.0, 20.0]), volume_timeseries)
        self.assertEqual(SparseTimeseriesStub(date, [20.0, 40.0]), chloride_timeseries)

    def test_b(self):
        """Test the incoming volume and chloride levels.

        There is only seepage incoming.

        """
        date = datetime(2012, 1, 18)

        precipitation = SparseTimeseriesStub()
        seepage = SparseTimeseriesStub(date, [5.0, 10.0])
        volumes = [precipitation, seepage]

        precipitation_chloride = 2.0
        seepage_chloride = 6.0
        concentrations = [precipitation_chloride, seepage_chloride]

        incoming = TotalVolumeChlorideTimeseries(volumes, concentrations)
        volume_timeseries, chloride_timeseries = incoming.compute()

        self.assertEqual(SparseTimeseriesStub(date, [5.0, 10.0]), volume_timeseries)
        self.assertEqual(SparseTimeseriesStub(date, [30.0, 60.0]), chloride_timeseries)
