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

class TimeSeriesDictOperator(object):

    def __init__(self, time_series):
        self.time_series = time_series

    def operate(self, time_series_dict, key):
        """Operate on time_series_dict[key].

        This method is abstract and should be implemented in a subclass.

        """
        assert False

    def as_dict(self, file_name):
        time_series_dict = self.time_series.as_dict(file_name)
        for key, time_serie in time_series_dict.items():
            self.operate(time_series_dict, key)
        return time_series_dict


class SwitchSign(TimeSeriesDictOperator):
    """Switches the sign of relevant time series.

    Instance parameter:
      *relevant_parameters*
        parameter names of relevant time series

    """
    def __init__(self, time_series, relevant_parameters):
        TimeSeriesDictOperator.__init__(self, time_series)
        self.relevant_parameters = relevant_parameters

    def operate(self, time_series_dict, key):
        """Switch the sign of the given time series when relevant."""
        parameter = key[1]
        if parameter in self.relevant_parameters:
            time_series_dict[key] = time_series_dict[key] * -1.0


class Filter(TimeSeriesDictOperator):
    """Removes the irrelevant time series.

    Instance parameter:
      *relevant_parameters*
        parameter names of relevant time series

    """
    def __init__(self, time_series, relevant_parameters):
        TimeSeriesDictOperator.__init__(self, time_series)
        self.relevant_parameters = relevant_parameters

    def operate(self, time_series_dict, key):
        """Remove the given time series when irrelevant."""
        parameter = key[1]
        if not parameter in self.relevant_parameters:
            del time_series_dict[key]

class FilterFractions(TimeSeriesDictOperator):
    """Removes the non-fractions time series."""
    def __init__(self, time_series):
        TimeSeriesDictOperator.__init__(self, time_series)

    def operate(self, time_series_dict, key):
        """Remove the given time series when irrelevant."""
        parameter = key[1]
        if not parameter.startswith('fraction_'):
            del time_series_dict[key]


class NegateSign(TimeSeriesDictOperator):
    """Set the time series of outgoing pumping stations to negative.

    Instance parameter:
      *outgoing_pumping_stations*
        locations of outgoing pumping stations

    """
    def __init__(self, time_series, outgoing_pumping_stations):
        TimeSeriesDictOperator.__init__(self, time_series)
        self.outgoing_pumping_stations = outgoing_pumping_stations

    def operate(self, time_series_dict, key):
        """Set the given time series to negative when outgoing."""
        location = key[0]
        if location in self.outgoing_pumping_stations:
            time_series_dict[key] = abs(time_series_dict[key]) * -1.0

