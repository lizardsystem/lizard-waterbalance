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
    """Implements a test suite for ConcentrationComputer::compute."""

    def setUp(self):
        self.concentrations = ConcentrationComputer()
        self.concentrations.initial_concentration = 30.0 # [g/m3]
        self.concentrations.initial_volume = 100.0 # [m3]

    def test_a(self):
        """Test without incoming volumes and outgoing volumes without chloride.

        Each time series has a single event.

        """
        self.set_timeseries(incoming_volumes=               [0.0],
                            incoming_chlorides=             [0.0],
                            outgoing_volumes=             [-20.0],
                            outgoing_volumes_no_chloride=   [0.0])
        self.assertEqual(self.timeseries(30.0), self.concentrations.compute())

    def set_timeseries(self, *args, **kwargs):
        for attribute, values in kwargs.items():
            timeseries = self.timeseries(*values)
            setattr(self.concentrations, attribute, timeseries)

    def timeseries(self, *args, **kwargs):
        date = datetime(2012, 1, 12)
        return SparseTimeseriesStub(date, list(args))

    def test_b(self):
        """Test without incoming volumes and outgoing volumes without chloride.

        Each time series has multiple events.

        """
        self.set_timeseries(incoming_volumes=               [0.0,   0.0],
                            incoming_chlorides=             [0.0,   0.0],
                            outgoing_volumes=             [-20.0, -30.0],
                            outgoing_volumes_no_chloride=   [0.0,   0.0])
        self.assertEqual(self.timeseries(30.0, 30.0), self.concentrations.compute())

    def test_c(self):
        """Test without incoming volumes but with outgoing volumes without chloride.

        Each time series has a single event.

        """
        self.set_timeseries(incoming_volumes=               [0.0],
                            incoming_chlorides=             [0.0],
                            outgoing_volumes=             [-10.0],
                            outgoing_volumes_no_chloride= [-10.0])
        self.assertEqual(self.timeseries(300.0 / 9.0), self.concentrations.compute())

    def test_d(self):
        """Test with incoming volumes s but with outgoing volumes without chloride.

        Each time series has multiple events.

        """
        self.set_timeseries(incoming_volumes=             [ 20.0,  10.0],
                            incoming_chlorides=           [200.0, 250.0],
                            outgoing_volumes=             [-30.0, -10.0],
                            outgoing_volumes_no_chloride= [  0.0,   0.0])
        expected_timeseries = \
            self.timeseries(((90.0 / 120.0) * 3200.0) / 90.0, \
                            ((90.0 / 100.0) * 2650.0) / 90.0)
        self.assertEqual(expected_timeseries, self.concentrations.compute())

    def test_e(self):
        """Test without volume, the concentration is 0.0

        Each time series has a single event.

        """
        self.concentrations.initial_volume = 0.0
        self.set_timeseries(incoming_volumes=             [  0.0],
                            incoming_chlorides=           [  0.0],
                            outgoing_volumes=             [-20.0],
                            outgoing_volumes_no_chloride= [  0.0])
        self.assertEqual(self.timeseries(0.0), self.concentrations.compute())

    def test_f(self):
        """Test that more volume going out than possible, the concentration is 0.0

        Each time series has a single event.

        """
        self.concentrations.initial_volume = 10.0

        self.set_timeseries(incoming_volumes=             [  0.0],
                            incoming_chlorides=           [  0.0],
                            outgoing_volumes=             [-20.0],
                            outgoing_volumes_no_chloride= [  0.0])
        self.assertEqual(self.timeseries(0.0), self.concentrations.compute())


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
