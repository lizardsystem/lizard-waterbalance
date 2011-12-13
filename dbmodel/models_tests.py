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

import unittest

from mock import Mock

from models import PumpingStation

class PumpingStationTests(unittest.TestCase):

    def setUp(self):
        self.concentration = Mock()
        self.concentration.stof_lower_concentration = 0.2
        self.concentration.stof_increment = 0.4

    def test_a(self):
        """Test that a single concentration is set correctly."""
        station = PumpingStation(None, None)
        station._find_concentration = lambda : self.concentration
        new_attr_names = {}
        new_attr_names["min_concentr_phosphate"] = "stof_lower_concentration"
        station.set_concentrations(new_attr_names)
        self.assertEqual(0.2, station.min_concentr_phosphate)

    def test_b(self):
        """Test that multiple concentrations are set correctly."""
        station = PumpingStation(None, None)
        station._find_concentration = lambda : self.concentration
        new_attr_names = {}
        new_attr_names["min_concentr_phosphate"] = "stof_lower_concentration"
        new_attr_names["incr_concentr_phosphate"] = "stof_increment"
        station.set_concentrations(new_attr_names)
        self.assertEqual(0.2, station.min_concentr_phosphate)
        self.assertEqual(0.4, station.incr_concentr_phosphate)
