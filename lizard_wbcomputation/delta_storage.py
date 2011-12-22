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
        # [get_storage_timeseries] is a function that returns the storage time
        # series given a start and end date
        self.get_storage_timeseries = get_storage_timeseries

    def compute(self, start_date, end_date):
        """Return the delta storage time series.

        If the storage at the date that precedes the start date is unknown,
        which is probable, this method cannot compute the delta storage at the
        start date. Therefore this function explicitly sets the delta storage
        at that date to 0.0.
        """
        delta_storage_timeseries = SparseTimeseriesStub()
        storage_timeseries = self.get_storage_timeseries(start_date, end_date)
        storage = self._get_first_value(storage_timeseries)
        for event in storage_timeseries.events(start_date, end_date):
            delta_storage_timeseries.add_value(event[0], event[1] - storage)
            storage = event[1]
        return delta_storage_timeseries

    def _get_first_value(self, storage_timeseries):
        """Return the value of the first event of the given time series."""
        return next(storage_timeseries.events(), (None, None))[1]
