#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Implements tests for the management command to compute and export a waterbalance."""

# This package implements the management commands for lizard-waterbalance Django
# app.
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
import os
import pkg_resources

from lizard_waterbalance.management.commands.compute_export import write_to_pi_file
from timeseries.timeseries import TimeSeries
from timeseries.timeseriesstub import SparseTimeseriesStub


def test_sorted_event_keys():
    """Test the way to attach a method to a TimeseriesStub-like object."""
    timeseries = \
        SparseTimeseriesStub(datetime(2011, 10, 25), [10.0, 20.0, 30.0])
    timeseries.sorted_event_items = lambda : list(timeseries.events())
    assert timeseries.sorted_event_items() == list(timeseries.events())

def test_write_to_pi_file():
    """Test the way to write a TimeseriesStub-like object to a PI XML file."""
    timeseries = \
        SparseTimeseriesStub(datetime(2011, 10, 25), [10.0, 20.0, 30.0])

    testdata = pkg_resources.resource_filename("lizard_waterbalance", "testdata/")
    filename = "sluice-error.xml"
    filepath = os.path.join(testdata, filename)
    if filename in os.listdir(testdata):
        os.remove(filepath)

    write_to_pi_file(location_id="SAP", parameter_id="sluice-error",
        filename=filepath, timeseries=timeseries)

    obj = TimeSeries.as_dict(filepath)

    assert obj[("SAP", "sluice-error")].get_events() == list(timeseries.events())





