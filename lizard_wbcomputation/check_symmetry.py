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

from optparse import OptionParser

from timeseries.timeseries import TimeSeries

from lizard_wbcomputation.check_fractions import Fractions


OUTGOING_PUMPING_STATIONS = [
    '3201_PS3',
    ]

PARAMETERS_TO_SWITCH = [
    'delta_storage',
    ]

RELEVANT_PARAMETERS = [
    'Q',
    'delta_storage',
    'discharge_drainage',
    'discharge_drained',
    'discharge_flow_off',
    'discharge_hardened',
    'discharge_sewer',
    'indraft',
    'precipitation',
    'evaporation',
    'seepage',
    'infiltration',
    'sluice_error',
    ]


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


def main():
    parser = OptionParser(usage="usage: %prog <PI XML time series file>")
    (options, args) = parser.parse_args()
    if len(args) == 1:
        reader = \
            SummedTimeSeriesReader(
                SwitchSign(
                    NegateSign(
                        Filter(TimeSeries,
                               relevant_parameters=RELEVANT_PARAMETERS),
                        outgoing_pumping_stations=OUTGOING_PUMPING_STATIONS),
                relevant_parameters=PARAMETERS_TO_SWITCH).as_dict)

        fractions = Fractions(reader)
        fractions.target_value = 0.0
        if fractions.verify(args[0]):
            return_code = 0
        else:
            return_code = 2
    else:
        parser.print_help()
        return_code = 1
    return return_code
