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

from lizard_waterbalance.sluice_error_computer import SluiceErrorComputer
from lizard_waterbalance.models import OpenWater
from timeseries.timeseriesstub import TimeseriesStub

def stub_empty_timeseries(only_input=False):
    """Return the empty list of volume timeseries.

    This function assumes there is no intake or pump. This means that this
    function can ignore parameter only_input.

    """
    return []

def stuba_retrieve_incoming_timeseries(only_input=False):
    """Return the dictionary of intake to measured time series.

    This function assumes there is a single intake that is not used for level
    control. This means that this function can ignore parameter only_input.

    """
    # We need to construct a dictionary of intake to time series. As we are not
    # interested in the intake, we use the value 0 for the intake even though 0
    # is not a valid PumpingStation. As long as we do not use 0 for an intake,
    # we get away with it.
    return {0: TimeseriesStub((datetime(2011, 3, 9), 8))}

class TestCasesWithoutPumpingStations(TestCase):

    def setUp(self):
        self.today = datetime(2011, 3, 9)
        self.tomorrow = self.today + timedelta(1)
        self.open_water = OpenWater()

    def test_a(self):
        """Test the case that the computed and measured timeseries are equal."""
        level_control = (TimeseriesStub((self.today, 0)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 0))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_b(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicate volume should be coming in via a
        non-existing intake.

        """
        level_control = (TimeseriesStub((self.today, 2)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 2))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_c(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicate volume should be going out via a
        non-existing pump.

        """
        level_control = (TimeseriesStub((self.today, 0)),
                         TimeseriesStub((self.today, -2)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, -2))
        self.assertEqual(expected_sluice_error, sluice_error)


class TestCasesWithaSingleIntake(TestCase):

    def setUp(self):
        self.today = datetime(2011, 3, 9)
        self.tomorrow = self.today + timedelta(1)
        self.open_water = OpenWater()
        self.open_water.retrieve_incoming_timeseries = stuba_retrieve_incoming_timeseries

    def test_a(self):
        """Test the case that the computed and measured timeseries are equal."""
        level_control = (TimeseriesStub((self.today, 0)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 0))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_b(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicate more volume is coming in via a
        non-existing intake.

        """
        level_control = (TimeseriesStub((self.today, 2)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 2))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_c(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicate more volume is going out via a
        non-existing pump.
        """
        level_control = (TimeseriesStub((self.today, 0)),
                         TimeseriesStub((self.today, -2)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, -2))
        self.assertEqual(expected_sluice_error, sluice_error)


def stubb_retrieve_incoming_timeseries(only_input=False):
    """Return the dictionary of intake to measured time series.

    This function assumes there is a single intake that is used for level
    control.

    """
    intake2timeseries = {}
    if not only_input:
        # We need to construct a dictionary of intake to time series. As we are
        # not interested in the intake, we use the value 0 for the intake even
        # though 0 is not a valid PumpingStation. As long as we do not use 0
        # for an intake, we get away with it.
        intake2timeseries[0] = TimeseriesStub((datetime(2011, 3, 9), 8))
    return intake2timeseries


class TestCasesWithaSingleIntakeUsedForLevelControl(TestCase):

    def setUp(self):
        self.today = datetime(2011, 3, 9)
        self.tomorrow = self.today + timedelta(1)
        self.open_water = OpenWater()
        self.open_water.retrieve_incoming_timeseries = stubb_retrieve_incoming_timeseries

    def test_a(self):
        """Test the case that the computed and measured timeseries are equal."""
        level_control = (TimeseriesStub((self.today, 8)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 0))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_b(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicates more volume is coming in via the
        intake.

        """
        level_control = (TimeseriesStub((self.today, 10)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 2))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_c(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicates less volume is coming in via the
        intake.

        """
        level_control = (TimeseriesStub((self.today, 6)),
                         TimeseriesStub((self.today, 0)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, -2))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_d(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicates volume is going out via the
        non-existing pump.

        """
        level_control = (TimeseriesStub((self.today, 0)),
                         TimeseriesStub((self.today, -2)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, -10))
        self.assertEqual(expected_sluice_error, sluice_error)

def stubb_retrieve_outgoing_timeseries(only_input=False):
    """Return the dictionary of pump to measured time series.

    This function assumes there is a single pump that is used for level
    control.

    """
    intake2timeseries = {}
    if not only_input:
        # We need to construct a dictionary of pump to time series. As we are
        # not interested in the pump, we use the value 0 for the pump even
        # though 0 is not a valid PumpingStation. As long as we do not use 0
        # for an pump, we get away with it.
        intake2timeseries[0] = TimeseriesStub((datetime(2011, 3, 9), -6))
    return intake2timeseries

class TestCasesWithaSingleIntakeAndSinglePumpBothUsedForLevelControl(TestCase):

    def setUp(self):
        self.today = datetime(2011, 3, 9)
        self.tomorrow = self.today + timedelta(1)
        self.open_water = OpenWater()
        self.open_water.retrieve_incoming_timeseries = stubb_retrieve_incoming_timeseries
        self.open_water.retrieve_outgoing_timeseries = stubb_retrieve_outgoing_timeseries

    def test_a(self):
        """Test the case that the computed and measured timeseries are equal."""
        level_control = (TimeseriesStub((self.today, 8)),
                         TimeseriesStub((self.today, -6)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 0))
        self.assertEqual(list(expected_sluice_error.events()), list(sluice_error.events()))

    def test_b(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicates more volume is coming in via the
        intake.

        """
        level_control = (TimeseriesStub((self.today, 10)),
                         TimeseriesStub((self.today, -6)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 2))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_c(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicate less volume is coming in via the
        intake.

        """
        level_control = (TimeseriesStub((self.today, 6)),
                         TimeseriesStub((self.today, -6)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, -2))
        self.assertEqual(expected_sluice_error, sluice_error)

    def test_d(self):
        """Test the case that the computed and measured timeseries differ.

        The computed timeseries indicates more volume is going out via the
        pump.

        """
        level_control = (TimeseriesStub((self.today, 8)),
                         TimeseriesStub((self.today, -4)))
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(self.open_water, level_control,
                                        self.today, self.tomorrow)
        expected_sluice_error = TimeseriesStub((self.today, 2))
        self.assertEqual(expected_sluice_error, sluice_error)
