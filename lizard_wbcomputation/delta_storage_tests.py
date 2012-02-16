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

from datetime import datetime
from unittest import TestCase

from lizard_wbcomputation.delta_storage import DeltaStorage
from timeseries.timeseriesstub import SparseTimeseriesStub

class DeltaStorageTests(TestCase):

    def test_a(self):
        """Test the computation of a DeltaStorage."""
        start = datetime(2011, 12, 21)
        values = [1.0, 3.0, 6.0]
        get_storage_timeseries = lambda s, e: SparseTimeseriesStub(start, values)
        get_initial_storage = lambda date: 0.0
        ds = DeltaStorage(get_storage_timeseries, get_initial_storage)
        ds_timeseries = ds.compute(start, datetime(2011, 12, 24))
        self.assertEqual(SparseTimeseriesStub(start, [1.0, 2.0, 3.0]),
                         ds_timeseries)
