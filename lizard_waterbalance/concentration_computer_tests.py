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

from lizard_waterbalance.concentration_computer import ConcentrationComputer
from lizard_waterbalance.timeseriesstub import TimeseriesStub

class ConcentrationComputerTests(TestCase):

    def test_a(self):
        """Test the case with one timeseries on one day."""
        today = datetime(2011, 2, 2)
        timeseries_list = [TimeseriesStub((today, 10.0))]
        concentration_list = [70]

        timeseries = ConcentrationComputer().compute(timeseries_list, concentration_list)
        self.assertEqual(TimeseriesStub((today, 700000.0)), timeseries)

    def test_b(self):
        """Test the case with one timeseries on two days."""
        today = datetime(2011, 2, 2)
        tomorrow = datetime(2011, 2, 3)
        timeseries_list = [TimeseriesStub((today, 10.0), (tomorrow, 20.0))]
        concentration_list = [70]

        timeseries = ConcentrationComputer().compute(timeseries_list, concentration_list)
        self.assertEqual(TimeseriesStub((today, 700000.0), (tomorrow, 1400000.0)), timeseries)

    def test_c(self):
        """Test the case with two timeseries on two days."""
        today = datetime(2011, 2, 2)
        tomorrow = datetime(2011, 2, 3)
        timeseries_list = [TimeseriesStub((today, 10.0), (tomorrow, 20.0)),
                           TimeseriesStub((today, 30.0), (tomorrow, 40.0))]
        concentration_list = [70, 10]
        timeseries = ConcentrationComputer().compute(timeseries_list, concentration_list)
        self.assertEqual(TimeseriesStub((today, 1000000.0), (tomorrow, 1800000.0)), timeseries)

