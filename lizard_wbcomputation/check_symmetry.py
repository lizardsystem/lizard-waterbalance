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

from lizard_wbcomputation.summed_time_series_reader import SummedTimeSeriesReader
from lizard_wbcomputation.target_value_checker import TargetValueChecker
from lizard_wbcomputation.time_series_dict_operator import Filter
from lizard_wbcomputation.time_series_dict_operator import NegateSign
from lizard_wbcomputation.time_series_dict_operator import SwitchSign


OUTGOING_PUMPING_STATIONS = [
    '6480_inlaatPB',
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

def main(args):
    parser = OptionParser(usage="usage: %prog <PI XML time series file>")
    (options, args) = parser.parse_args(args)
    if len(args) == 1:
        reader = \
            SummedTimeSeriesReader(
                SwitchSign(
                    NegateSign(
                        Filter(TimeSeries,
                               relevant_parameters=RELEVANT_PARAMETERS),
                        outgoing_pumping_stations=OUTGOING_PUMPING_STATIONS),
                relevant_parameters=PARAMETERS_TO_SWITCH).as_dict)

        target_value_checker = TargetValueChecker(reader)
        target_value_checker.target_value = 0.0
        if target_value_checker.verify(args[0]):
            return_code = 0
        else:
            return_code = 2
    else:
        parser.print_help()
        return_code = 1
    return return_code
