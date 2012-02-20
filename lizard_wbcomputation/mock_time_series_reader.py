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

from mock import Mock

from timeseries.timeseries import TimeSeries

class MockTimeSeriesReader(object):

    def __init__(self, *args):
        self.get = Mock(return_value=create_time_series(*args))


class MockTimeSeries(object):

    def __init__(self, *args):
        self.input = {}
        for time_series_spec in args:
            location, parameter = time_series_spec[0:2]
            values = time_series_spec[2:]
            self.input[(location, parameter)] = create_time_series(*values)

    def as_dict(self, file_name):
        return self.input

def create_time_series(*args):
    time_series = TimeSeries()
    for index, value in enumerate(args):
        time_series[datetime(2012, 2,  9 + index, 23, 0)] = value
    return time_series
