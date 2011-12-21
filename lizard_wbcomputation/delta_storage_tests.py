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
from datetime import timedelta
from unittest import TestCase

from mock import Mock

from lizard_wbcomputation.delta_storage import DeltaStorage
from timeseries.timeseriesstub import SparseTimeseriesStub

class DeltaStorageTests(TestCase):

    def test_a(self):
        """Test the construction of a DeltaStorage."""
        storage_timeseries = \
            SparseTimeseriesStub(datetime(2011, 12, 21), [1.0, 3.0, 6.0])
        waterbalance_computer = Mock()
        waterbalance_computer.get_level_control_timeseries = \
            lambda s,e: {'storage': storage_timeseries}
        start = datetime(2011, 12, 21)
        end = start + timedelta(len(list(storage_timeseries.events())))
        delta_storage_timeseries = DeltaStorage(waterbalance_computer).compute(start, end)
        expected_delta_storage_timeseries = SparseTimeseriesStub(datetime(2011, 12, 21), [1.0, 2.0, 3.0])
        self.assertEqual(list(expected_delta_storage_timeseries.events()),
                         list(delta_storage_timeseries.events()))
