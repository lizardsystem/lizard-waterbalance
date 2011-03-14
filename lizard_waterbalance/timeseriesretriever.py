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

from timeseries.timeseriesstub import TimeseriesStub
from timeseries.timeseriesstub import TimeseriesWithMemoryStub

from filereader import FileReader

class TimeseriesRetriever:
    """Retrieves the time series stored in an ASCII file.

    Instance variables:
    * filereader -- interface to the ASCII file
    * code2name -- dictionary that maps each time serie code to time serie name
    * incomplete_timeseries -- names of time series with missing dates

    """
    def __init__(self):
        self.filereader = FileReader()
        self.code2name = dict([("A_0_0", "precipitation"),
                               ("A_0_1", "evaporation"),
                               ("O_0_0_0", "seepage"),
                               ("O_0_1_0", "infiltration"),
                               ("O_0_2", "minimum level"),
                               ("O_0_3", "maximum level"),
                               ("O_0_4", "target level"),
                               ("O_0_6", "volume"),
                               ("PS_0", "Inlaat Vecht"),
                               ("PS_1", "dijklek"),
                               ("PS_2", "inlaat peilbeheer")])

        self.incomplete_timeseries = ["seepage", "minimum level", "maximum level", "Inlaat Vecht", "dijklek", "inlaat peilbeheer"]

    def read_timeseries(self, filename):
        """Retrieve the time series in the ASCII file with the given name."""
        self.timeseries = {}
        self.filereader.open(filename)
        first_line = True
        for line in self.filereader.readlines():
            if first_line:
                first_line = False
            else:
                fields = line.split(',')
                name = self.find_name(fields[0])
                date = datetime(int(fields[1]), int(fields[2]), int(fields[3]))
                value = float(fields[4])
                if name in self.incomplete_timeseries:
                    self.timeseries.setdefault(name, TimeseriesWithMemoryStub()).add_value(date, value)
                else:
                    self.timeseries.setdefault(name, TimeseriesStub()).add_value(date, value)
        self.filereader.close()

    def find_name(self, code):
        """Return the complete name of the time series with the given code."""
        timeseries_name = ""
        for key, value in self.code2name.items():
            if key == code[0:len(key)]:
                timeseries_name = value
        return timeseries_name

    def get_timeseries(self, name):
        """Return the TimeseriesStub with the given name."""
        return self.timeseries[name]

