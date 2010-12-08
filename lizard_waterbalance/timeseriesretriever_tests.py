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
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
# Initial date:       2010-12-06
#
#******************************************************************************

from datetime import datetime
from unittest import TestCase

from filereader import FileReaderStub
from timeseriesretriever import TimeseriesRetriever


class TimeserieRetrieverSuite(TestCase):

    def test_a(self):
        """Test a TimeserieRetriever retrieves the correct event.

        This test also tests that a TimeserieRetriever skips the first line of
        the file, which contains the names of each field.

        """
        file_contents = ["code,year,month,day,value", "A_0_0_0,1996,1,2,0.0"]
        retriever = TimeseriesRetriever()
        retriever.filereader = FileReaderStub(file_contents)
        retriever.read_timeseries("timeseries.csv")
        expected_events = [(datetime(1996, 1, 2), 0.0)]
        timeseries = retriever.get_timeseries("precipitation")
        self.assertEqual(expected_events, list(timeseries.events()))

    def test_b(self):
        """Test a TimeserieRetriever retrieves the correct events."""
        file_contents = ["code,year,month,day,value",
                         "A_0_0_0,1996,1,2,0.0",
                         "A_0_1_0,1996,1,2,0.2"]
        retriever = TimeseriesRetriever()
        retriever.filereader = FileReaderStub(file_contents)
        retriever.read_timeseries("timeseries.csv")
        expected_events = [(datetime(1996, 1, 2), 0.0)]
        timeseries = retriever.get_timeseries("precipitation")
        self.assertEqual(expected_events, list(timeseries.events()))
        expected_events = [(datetime(1996, 1, 2), 0.2)]
        timeseries = retriever.get_timeseries("evaporation")
        self.assertEqual(expected_events, list(timeseries.events()))

