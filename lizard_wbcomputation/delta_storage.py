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

from datetime import timedelta

from timeseries.timeseriesstub import SparseTimeseriesStub


class DeltaStorage:

    def __init__(self, get_storage_timeseries, get_delta_storage):
        # [get_storage_timeseries] is a function that returns the storage time
        # series given a start and end date
        self.get_storage_timeseries = get_storage_timeseries
        # [get_delta_storage] is a function that returns the latest delta
        # storage at a given date
        self.get_delta_storage = get_delta_storage

    def compute(self, start_date, end_date):
        """Return the delta storage time series.

        If the storage at the date that precedes the start date is unknown,
        which is probable, this method cannot compute the delta storage at the
        start date. Therefore this function explicitly sets the delta storage
        at that date to 0.0.
        """
        delta_storage_timeseries = SparseTimeseriesStub()
        storage_timeseries = self.get_storage_timeseries(start_date, end_date)
        storage = None
        for event in storage_timeseries.events(start_date, end_date):
            # the date of the initial event can be later than the specified
            # start date
            if storage is None:
                storage = event[1] - self.get_delta_storage(event[0])
            delta_storage_timeseries.add_value(event[0], event[1] - storage)
            storage = event[1]
        return delta_storage_timeseries
