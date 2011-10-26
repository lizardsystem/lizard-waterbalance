#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Implements tests for the command to compute and export a waterbalance."""

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
import unittest

from mock import Mock

from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceScenario
from lizard_waterbalance.management.commands.compute_export import Command
from timeseries.timeseriesstub import TimeseriesStub

class CommandTests(unittest.TestCase):

    def test_a(self):
        """Test that the invocation finds the right configuration."""

        area = WaterbalanceArea()
        area.name = "Aetsveldse polder Oost"
        area.save()
        scenario = WaterbalanceScenario()
        scenario.name = "import"
        scenario.save()
        configuration = WaterbalanceConf()
        configuration.waterbalance_area = area
        configuration.waterbalance_scenario = scenario
        configuration.calculation_start_date = datetime(2011, 10, 26)
        configuration.calculation_end_date = datetime(2011, 10, 26)
        configuration.save()

        command = Command()
        command.create_computer = Mock()
        command.handle("aetsveldse-polder-oost", "import")

        configuration = command.create_computer.call_args[0][0]
        self.assertEqual(configuration.waterbalance_area.slug, "aetsveldse-polder-oost")
        self.assertEqual(configuration.waterbalance_scenario.slug, "import")
