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


class SummedFractionsReader(object):

    def get(self, file_name):
        return reduce(lambda x, y: x + y, self.fraction_timeseries_list)


class Fractions(object):

    def __init__(self, fractions_reader):
        self.fractions_reader = fractions_reader

    def verify(self, file_name):
        success = True
        fraction_timeseries = self.fractions_reader.get(file_name)
        for date, value in fraction_timeseries.get_events():
            event_value = value[0]
            success = event_value > 1 - 1e-6 and event_value < 1 + 1e-6
            if not success:
                break
        return success


def main():
    parser = OptionParser(usage="usage: %prog <PI XML time series file>")
    (options, args) = parser.parse_args()
    if len(args) == 1:
        if Fractions().verify(args[0]):
            return_code = 0
        else:
            return_code = 2
    else:
        parser.print_help()
        return_code = 1
    return return_code
