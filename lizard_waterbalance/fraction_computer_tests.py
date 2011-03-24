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

from mock import Mock
from mock import ReturnValues

from lizard_waterbalance.bucket_summarizer import BucketsSummary
from lizard_waterbalance.fraction_computer import FractionComputer
from lizard_waterbalance.models import OpenWater
from timeseries.timeseriesstub import TimeseriesStub


class FractionComputerTests(TestCase):
    """Contains tests for the fraction computation of an open water."""

    def setUp(self):
        """Create the fixture for the tests in this suite."""
        self.open_water = OpenWater()
        self.open_water.surface = 100
        self.open_water.init_water_level = 1.0
        self.open_water.crop_evaporation_factor = 1.0
        self.open_water.bottom_height = 0.9
        self.today = datetime(2011, 1, 30)
        self.buckets_summary = BucketsSummary()

#    def test_a(self):
#        """Test the initial fraction on a single day."""
#        fraction_computer = FractionComputer()
#        buckets_summary = BucketsSummary()
#        vertical_timeseries = [TimeseriesStub(),
#                               TimeseriesStub(),
#                               TimeseriesStub(),
#                               TimeseriesStub()]
#        storage = TimeseriesStub((self.today, 10.0))
#        intakes_timeseries = []
#        fractions = fraction_computer.compute(self.open_water,
#                                              buckets_summary,
#                                              vertical_timeseries,
#                                              storage,
#                                              intakes_timeseries)
#        expected_initial_fractions = TimeseriesStub((self.today, 1.0))
#        self.assertEqual(expected_initial_fractions, fractions[0])
#
#    def test_b(self):
#        """Test the initial fraction on a single day.
#
#        The computation of the initial fraction depends on the storage time
#        series and on methods FractionComputer.initial_storage and
#        FractionComputer.delta_out. We stub these methods out to make it more
#        easy to create the tests.
#
#        """
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        mock_delta_out = Mock({"delta_out": 0.0})
#        fraction_computer.delta_out = mock_delta_out.delta_out
#        storage = TimeseriesStub((self.today, 10.0))
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage,
#                                              []) # don't care
#        expected_initial_fractions = TimeseriesStub((self.today, 1.0))
#        self.assertEqual(expected_initial_fractions, fractions[0])
#
#    def test_c(self):
#        """Test the initial fraction on a single day.
#
#        We test the case that there is volume incoming on the first day.
#
#        """
#        storage = TimeseriesStub((self.today, 10.0))
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        mock_total_incoming = Mock({"total_incoming": 2.0})
#        fraction_computer.total_incoming = mock_total_incoming.total_incoming
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage, # don't care
#                                              [TimeseriesStub((self.today, 2.0))])
#        expected_initial_fractions = TimeseriesStub((self.today, 10.0 / 12.0))
#        self.assertEqual(list(expected_initial_fractions.events()), list(fractions[0].events()))
#
#    def test_ca(self):
#        """Test the initial fraction on a single day.
#
#        We test the case that there is volume incoming and volume outging on
#        the first day.
#
#        """
#        storage = TimeseriesStub((self.today, 11.0))
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        mock_total_incoming = Mock({"total_incoming": 2.0})
#        fraction_computer.total_incoming = mock_total_incoming.total_incoming
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage, # don't care
#                                              [TimeseriesStub((self.today, 2.0))])
#        expected_initial_fractions = TimeseriesStub((self.today, 10.0 / 12.0))
#        self.assertEqual(expected_initial_fractions, fractions[0])
#
#    def test_d(self):
#        """Test the initial fraction on two days.
#
#        We test the case that there is no volume incoming.
#
#        """
#        tomorrow = self.today + timedelta(1)
#        storage = TimeseriesStub((self.today, 10.0), (tomorrow, 10.0))
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        mock_total_incoming = Mock({"total_incoming": 0.0})
#        fraction_computer.total_incoming = mock_total_incoming.total_incoming
#
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage,
#                                              [])
#        expected_initial_fractions = TimeseriesStub((self.today, 1.0),
#                                                    (tomorrow, 1.0))
#        self.assertEqual(expected_initial_fractions, fractions[0])
#
#    def test_db(self):
#        """Test the initial fraction on two days.
#
#        We test the case that there is volume incoming on both days both no
#        volume outgoing.
#
#        """
#        tomorrow = self.today + timedelta(1)
#        storage = TimeseriesStub((self.today, 12.0), (tomorrow, 14.0))
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        mock_total_incoming = Mock({"total_incoming": 2.0})
#        fraction_computer.total_incoming = mock_total_incoming.total_incoming
#
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage,
#                                              [TimeseriesStub((self.today, 2.0), (tomorrow, 2.0))])
#        expected_initial_fractions = TimeseriesStub((self.today, 10.0 / 12.0),
#                                                    (tomorrow, 10.0 / 14.0))
#        self.assertEqual(list(expected_initial_fractions.events()), list(fractions[0].events()))
#
#    def test_dc(self):
#        """Test the initial fraction on two days.
#
#        We test the case that there is volume incoming and volume outgoing on
#        both days.
#
#        """
#        tomorrow = self.today + timedelta(1)
#        storage = TimeseriesStub((self.today, 11.0), (tomorrow, 13.0))
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        mock_total_incoming = Mock({"total_incoming": 2.0})
#        fraction_computer.total_incoming = mock_total_incoming.total_incoming
#
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage,
#                                              [TimeseriesStub((self.today, 2.0), (tomorrow, 2.0))])
#        initial_fraction = 10.0 / 12.0
#        expected_initial_fractions = TimeseriesStub((self.today, initial_fraction),
#                                                    (tomorrow, (initial_fraction * 11.0) / 13.0))
#        self.assertEqual(expected_initial_fractions, fractions[0])
#
#    def test_e(self):
#        """Test a single intake fraction on a single day.
#
#        The computation of the initial fraction depends on the storage time
#        series and on methods FractionComputer.initial_storage and
#        FractionComputer.delta_out. We stub these methods out to make it more
#        easy to create the tests.
#
#        """
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        storage = TimeseriesStub((self.today, 12.0))
#        intakes_timeseries = [TimeseriesStub((self.today, 2.0))]
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage,
#                                              intakes_timeseries)
#        expected_initial_fractions = TimeseriesStub((self.today, 2.0 / 12.0))
#        self.assertEqual(expected_initial_fractions, fractions[7])
#
#    def test_f(self):
#        """Test two intake fractions on a single day.
#
#        The computation of the initial fraction depends on the storage time
#        series and on methods FractionComputer.initial_storage and
#        FractionComputer.delta_out. We stub these methods out to make it more
#        easy to create the tests.
#
#        """
#        fraction_computer = FractionComputer()
#        mock_initial_storage = Mock({"initial_storage": 10.0})
#        fraction_computer.initial_storage = mock_initial_storage.initial_storage
#        storage = TimeseriesStub((self.today, 16.0))
#        intakes_timeseries = [TimeseriesStub((self.today, 2.0)),
#                              TimeseriesStub((self.today, 4.0))]
#        fractions = fraction_computer.compute(self.open_water,
#                                              BucketsSummary(),
#                                              [TimeseriesStub()] * 4, # don't care
#                                              storage,
#                                              intakes_timeseries)
#        expected_initial_fractions = (TimeseriesStub((self.today, 2.0 / 16.0)),
#                                      TimeseriesStub((self.today, 4.0 / 16.0)))
#        self.assertEqual(expected_initial_fractions[0], fractions[7])
#        self.assertEqual(expected_initial_fractions[1], fractions[8])

