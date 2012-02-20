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

class SummedTimeSeriesReader(object):
    """Implements the retrieval of the summed time series from a file.

    To retrieve all the time series from a given file, this class uses a
    function supplied to the constructor and that is stored as an instance
    attribute. This function returns all the time series as a dictionary that
    maps a (location, parameter) tuple to a time series.

    """

    def __init__(self, get_time_series_as_dict):
        self.get_time_series_as_dict = get_time_series_as_dict

    def get(self, file_name):
        """Returns the summed fraction time series from the given file."""
        time_series = self.get_time_series_as_dict(file_name).values()
        return reduce(lambda x, y: x + y, time_series)


