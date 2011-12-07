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

from lizard_wbcomputation.vertical_timeseries_computer import VerticalTimeseriesComputer
from timeseries.timeseriesstub import TimeseriesStub


class VerticalTimeseriesComputerTests(TestCase):
    """Contains tests for the VerticalTimeseriesComputer.

    The tests in this suite verify that LevelControlComputer computes the right
    sluice error.

    """

    def setUp(self):
        """Create the fixture for the tests in this suite."""
        self.surface = 100
        self.crop_evaporation_factor = 1.0
        self.today = datetime(2011, 1, 28)
        self.tomorrow = datetime(2011, 1, 29)

    def test_a(self):
        """Test the case with only positive seepage on a single day."""
        precipitation = TimeseriesStub((self.today, 4.0))
        evaporation = TimeseriesStub((self.today, 2.0))
        seepage = TimeseriesStub((self.today, 1.0))
        infiltration = TimeseriesStub((self.today, 0.0))
        vertical_timeseries = VerticalTimeseriesComputer()
        timeseries = vertical_timeseries.compute(self.surface,
                                                 self.crop_evaporation_factor,
                                                 precipitation,
                                                 evaporation,
                                                 seepage,
                                                 infiltration)
        expected_timeseries = {"precipitation":TimeseriesStub((self.today, .4)),
                               "evaporation":TimeseriesStub((self.today, -.2)),
                               "seepage":TimeseriesStub((self.today, .1)),
                               "infiltration":TimeseriesStub((self.today, 0))}
        self.assertEqual(list(expected_timeseries["precipitation"].events()), list(timeseries["precipitation"].events()))
        self.assertEqual(list(expected_timeseries["evaporation"].events()), list(timeseries["evaporation"].events()))
        self.assertEqual(list(expected_timeseries["seepage"].events()), list(timeseries["seepage"].events()))
        self.assertEqual(list(expected_timeseries["infiltration"].events()), list(timeseries["infiltration"].events()))

    def test_aa(self):
        """Test the case with only positive seepage on a single day.

        The crop evaporation factor is 0.5.

        """
        precipitation = TimeseriesStub((self.today, 4.0))
        evaporation = TimeseriesStub((self.today, 2.0))
        seepage = TimeseriesStub((self.today, 1.0))
        infiltration = TimeseriesStub((self.today, 0.0))
        vertical_timeseries = VerticalTimeseriesComputer()
        timeseries = vertical_timeseries.compute(self.surface,
                                                 0.5,
                                                 precipitation,
                                                 evaporation,
                                                 seepage,
                                                 infiltration)
        expected_timeseries = {"precipitation":TimeseriesStub((self.today, .4)),
                               "evaporation":TimeseriesStub((self.today, -.1)),
                               "seepage":TimeseriesStub((self.today, .1)),
                               "infiltration":TimeseriesStub((self.today, 0))}
        self.assertEqual(list(expected_timeseries["precipitation"].events()), list(timeseries["precipitation"].events()))
        self.assertEqual(list(expected_timeseries["evaporation"].events()), list(timeseries["evaporation"].events()))
        self.assertEqual(list(expected_timeseries["seepage"].events()), list(timeseries["seepage"].events()))
        self.assertEqual(list(expected_timeseries["infiltration"].events()), list(timeseries["infiltration"].events()))

    def test_b(self):
        """Test the case with only positive seepage on two days."""
        precipitation = TimeseriesStub((self.today, 4.0),
                                       (self.tomorrow, 6.0))
        evaporation = TimeseriesStub((self.today, 2.0),
                                     (self.tomorrow, 4.0))
        seepage = TimeseriesStub((self.today, 1.0),
                                 (self.tomorrow, 3.0))
        infiltration = TimeseriesStub((self.today, 0.0))
        vertical_timeseries = VerticalTimeseriesComputer()
        timeseries = vertical_timeseries.compute(self.surface,
                                                 self.crop_evaporation_factor,
                                                 precipitation,
                                                 evaporation,
                                                 seepage,
                                                 infiltration)
        expected_timeseries = {"precipitation":TimeseriesStub((self.today, .4),
                                              (self.tomorrow, .6)),
                               "evaporation":TimeseriesStub((self.today, -.2),
                                              (self.tomorrow, -.4)),
                               "seepage":TimeseriesStub((self.today, .1),
                                              (self.tomorrow, .3)),
                               "infiltration":TimeseriesStub((self.today, 0), (self.tomorrow, 0))}
        self.assertEqual(list(expected_timeseries["precipitation"].events()), list(timeseries["precipitation"].events()))
        self.assertEqual(list(expected_timeseries["evaporation"].events()), list(timeseries["evaporation"].events()))
        self.assertEqual(list(expected_timeseries["seepage"].events()), list(timeseries["seepage"].events()))
        self.assertEqual(list(expected_timeseries["infiltration"].events()), list(timeseries["infiltration"].events()))

    def test_c(self):
        """Test the case with both positive and negative seepage on two days."""
        precipitation = TimeseriesStub((self.today, 4.0),
                                       (self.tomorrow, 6.0))
        evaporation = TimeseriesStub((self.today, 2.0),
                                     (self.tomorrow, 4.0))
        seepage = TimeseriesStub((self.today, 1.0),
                                 (self.tomorrow, 0.0))
        infiltration = TimeseriesStub((self.today, 0.0),
                                      (self.tomorrow, -1.0))
        vertical_timeseries = VerticalTimeseriesComputer()
        timeseries = vertical_timeseries.compute(self.surface,
                                                 self.crop_evaporation_factor,
                                                 precipitation,
                                                 evaporation,
                                                 seepage,
                                                 infiltration)
        expected_timeseries = {"precipitation":TimeseriesStub((self.today, .4),
                                              (self.tomorrow, .6)),
                               "evaporation":TimeseriesStub((self.today, -.2),
                                              (self.tomorrow, -.4)),
                               "seepage":TimeseriesStub((self.today, .1),
                                              (self.tomorrow, 0)),
                               "infiltration":TimeseriesStub((self.today, 0),
                                              (self.tomorrow, -.1))}
        self.assertEqual(list(expected_timeseries["precipitation"].events()), list(timeseries["precipitation"].events()))
        self.assertEqual(list(expected_timeseries["evaporation"].events()), list(timeseries["evaporation"].events()))
        self.assertEqual(list(expected_timeseries["seepage"].events()), list(timeseries["seepage"].events()))
        self.assertEqual(list(expected_timeseries["infiltration"].events()), list(timeseries["infiltration"].events()))


