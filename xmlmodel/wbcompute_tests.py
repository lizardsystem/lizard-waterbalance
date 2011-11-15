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

from xmlmodel.wbcompute import insert_calculation_range

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
