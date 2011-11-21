#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The xml package provides the functionality to calculate the waterbalance for
# a waterbalance configuration specified in set of XML files.
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
from xml.dom.minidom import parseString

from mock import Mock

from nens import mock as nens_mock
from timeseries.timeseriesstub import TimeseriesStub
from timeseries.timeseriesstub import SparseTimeseriesStub
from xmlmodel.reader import Area
from xmlmodel.wbcompute import insert_calculation_range
from xmlmodel.wbcompute import WriteableTimeseries


class Tests(TestCase):

    def setUp(self):

        run_file_contents = '''\
<?xml version="1.0" encoding="UTF-8"?>
<Run xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.wldelft.nl/fews/PI" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_run.xsd" version="1.5">
    <timeZone>1.0</timeZone>
    <startDateTime date="2004-12-23" time="00:00:00"/>
    <endDateTime date="2011-11-16" time="00:00:00"/>
    <time0 date="2010-01-01" time="00:00:00"/>
    <workDir>data/Waterbalans/model</workDir>
    <inputParameterFile>data/deltares/input/Parameters.xml</inputParameterFile>
    <inputTimeSeriesFile>data/deltares/input/Tijdreeksen.xml</inputTimeSeriesFile>
    <outputDiagnosticFile>data/deltares/output/Diagnostics.xml</outputDiagnosticFile>
    <outputTimeSeriesFile>data/deltares/output/waterbalance-graph.xml</outputTimeSeriesFile>
    <properties>
        <string key="Regio" value="Waternet"/>
        <string key="Gebied" value="SAP"/>
    </properties>
</Run>
'''
        self.run_dom = parseString(run_file_contents)

    def test(self):
        """Function insert_calculation_range inserts the right start and end datetime."""
        run_info = {}
        insert_calculation_range(self.run_dom, run_info)
        self.assertEqual(datetime(2004, 12, 23), run_info['startDateTime'])
        self.assertEqual(datetime(2011, 11, 16), run_info['endDateTime'])

    def test_b(self):
        """Test the requirements for a TimeseriesStub to be writeable."""
        stream = nens_mock.Stream()
        timeseries = TimeseriesStub((datetime(2011, 11, 17), 10.0))
        timeseries.type = 'instantaneous'
        timeseries.location_id = 'SAP'
        timeseries.parameter_id = 'Q'
        timeseries.miss_val = '-999.0'
        timeseries.station_name = 'Huh?'
        timeseries.units = 'dag'
        TimeseriesStub.write_to_pi_file(stream, [timeseries])

    def test_c(self):
        """Test the requirements for a SparseTimeseriesStub to be writeable."""
        stream = nens_mock.Stream()
        timeseries = SparseTimeseriesStub(datetime(2011, 11, 17), [10.0])
        timeseries.type = 'instantaneous'
        timeseries.location_id = 'SAP'
        timeseries.parameter_id = 'Q'
        timeseries.miss_val = '-999.0'
        timeseries.station_name = 'Huh?'
        timeseries.units = 'dag'
        SparseTimeseriesStub.write_to_pi_file(stream, [timeseries])


class MoreTests(TestCase):

    def setUp(self):
        self.area = Area()
        self.area.location_id = 20111117
        self.label2parameter = {'hardened': 'discharge_hardened'}

    def test_a(self):
        writeable_timeseries = WriteableTimeseries(self.area,
                                                   self.label2parameter)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        self.assertEqual(1, len(writeable_timeseries.timeseries_list))

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(timeseries, single_timeseries)

    def test_b(self):
        writeable_timeseries = WriteableTimeseries(self.area,
                                                   self.label2parameter)

        timeseries = TimeseriesStub()
        writeable_timeseries.insert({'hardened': timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(20111117, single_timeseries.location_id)

    def test_c(self):
        """Test an empty dict of PumpingStation to TimeseriesStub."""
        writeable_timeseries = WriteableTimeseries(self.area,
                                                   self.label2parameter)

        writeable_timeseries.insert2({})

        self.assertEqual(0, len(writeable_timeseries.timeseries_list))

    def create_station(self):
        station = Mock()
        station.location_id = 20111121
        return station

    def test_d(self):
        """Test a dict of PumpingStation to TimeseriesStub of size 1."""
        writeable_timeseries = WriteableTimeseries(self.area,
                                                   self.label2parameter)

        station = self.create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert2({station: timeseries})

        self.assertEqual(1, len(writeable_timeseries.timeseries_list))
        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(timeseries, single_timeseries)

    def test_e(self):
        """Test the right location id is assigned.

        The writeable time series should have a location id equal to
        the location id of the pumping station.

        """
        writeable_timeseries = WriteableTimeseries(self.area,
                                                   self.label2parameter)

        station = self.create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert2({station: timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual(20111121, single_timeseries.location_id)

    def test_f(self):
        """Test the right parameter id is assigned.

        The writeable time series should have parameter id 'Q'.

        """
        writeable_timeseries = WriteableTimeseries(self.area,
                                                   self.label2parameter)

        station = self.create_station()
        timeseries = TimeseriesStub()
        writeable_timeseries.insert2({station: timeseries})

        single_timeseries = writeable_timeseries.timeseries_list[0]
        self.assertEqual('Q', single_timeseries.parameter_id)

