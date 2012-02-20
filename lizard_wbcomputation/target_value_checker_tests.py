#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The lizard_wbcomputation package implements the computational core of the
# lizard waterbalance Django app.er
#
# Copyright (C) 2012 Nelen & Schuurmans
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

from unittest import TestCase

from lizard_wbcomputation.check_fractions_tests import MockFractionsReader
from lizard_wbcomputation.target_value_checker import TargetValueChecker


class TargetValueChecker_verify_TestSuite(TestCase):

    def test_a(self):
        """Test for a single fraction time series whose values are always 1."""
        fractions = TargetValueChecker(MockFractionsReader(1.0, 1.0, 1.0))
        self.assertTrue(fractions.verify('waterbalance-graph.xml'))

    def test_b(self):
        """Test for a single fraction time series whose values are not always 1.

        """
        fractions = TargetValueChecker(MockFractionsReader(1.0, 0.8, 1.0))
        self.assertFalse(fractions.verify('waterbalance-graph.xml'))
