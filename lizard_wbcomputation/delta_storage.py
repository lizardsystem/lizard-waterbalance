#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The dbmodel package provides an interface to the data required by the
# computational core of the lizard waterbalance Django app. This data is stored
# in multiple databases.
#
# Copyright (C) 2011 Nelen & Schuurmans
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

from timeseries.timeseriesstub import SparseTimeseriesStub


class DeltaStorage:

    def __init__(self, get_storage_timeseries):
        self.get_storage_timeseries = get_storage_timeseries

    def compute(self, start_date, end_date):
        delta_storage_timeseries = SparseTimeseriesStub()
        storage, storage_timeseries = \
            self.get_storage_timeseries(start_date, end_date)
        for event in storage_timeseries.events():
            delta_storage_timeseries.add_value(event[0], event[1] - storage)
            storage = event[1]
        return delta_storage_timeseries
