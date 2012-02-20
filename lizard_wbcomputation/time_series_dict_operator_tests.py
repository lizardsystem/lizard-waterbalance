#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The lizard_wbcomputation package implements the computational core of the
# lizard waterbalance Django app.
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

from check_fractions_tests import MockTimeSeries
from check_fractions_tests import create_time_series

from lizard_wbcomputation.time_series_dict_operator import Filter
from lizard_wbcomputation.time_series_dict_operator import NegateSign
from lizard_wbcomputation.time_series_dict_operator import SwitchSign


class SwitchSign_as_dict_TestSuite(TestCase):

    def test_a(self):
        """Test a single time series that should not be switched.

        """
        time_series = SwitchSign(
            MockTimeSeries(('3201', 'delta_storage', 10.0, 20.0, 30.0)),
            relevant_parameters=[])
        time_series_dict = time_series.as_dict(file_name="don't care")
        expected_time_series = \
            MockTimeSeries(('3201', 'delta_storage', 10.0, 20.0, 30.0))
        self.assertEqual(expected_time_series.as_dict(file_name="don't care"),
                         time_series_dict)


    def test_b(self):
        """Test a single time series that should be switched.

        """
        time_series = SwitchSign(
            MockTimeSeries(('3201', 'delta_storage', 10.0, 20.0, 30.0)),
            relevant_parameters=['delta_storage'])
        time_series_dict = time_series.as_dict(file_name="don't care")
        expected_time_series = \
            MockTimeSeries(('3201', 'delta_storage', -10.0, -20.0, -30.0))
        self.assertEqual(expected_time_series.as_dict(file_name="don't care"),
                         time_series_dict)


    def test_c(self):
        """Test multiple time series one fo which should be switched.

        """
        time_series = SwitchSign(
            MockTimeSeries(('3201', 'delta_storage', 10.0, 20.0, 30.0),
                           ('3201', 'discharge_drained', 0.0, 2.0, 4.0)),
            relevant_parameters=['delta_storage'])
        time_series_dict = time_series.as_dict(file_name="don't care")
        expected_time_series = \
            MockTimeSeries(('3201', 'delta_storage', -10.0, -20.0, -30.0),
                           ('3201', 'discharge_drained', 0.0, 2.0, 4.0))
        self.assertEqual(expected_time_series.as_dict(file_name="don't care"),
                         time_series_dict)


class NegateSign_as_dict_TestSuite(TestCase):

    def test_a(self):
        """Test the setting of a single time series of an incoming time series.

        """
        time_series = NegateSign(
            MockTimeSeries(('3201', 'discharge_drained', 10.0, 20.0, 30.0)),
            outgoing_pumping_stations=[])
        time_series_dict = time_series.as_dict(file_name="don't care")
        expected_time_series = \
            MockTimeSeries(('3201', 'discharge_drained', 10.0, 20.0, 30.0))
        self.assertEqual(expected_time_series.as_dict(file_name="don't care"),
                         time_series_dict)

    def test_b(self):
        """Test the setting of a single time series of an outgoing time series.

        """
        time_series = NegateSign(
            MockTimeSeries(('3201_PS1', 'Q', 0.0, 1.0, 2.0)),
            outgoing_pumping_stations=['3201_PS1'])
        time_series_dict = time_series.as_dict(file_name="don't care")
        expected_time_series = \
            MockTimeSeries(('3201_PS1', 'Q', 0.0, -1.0, -2.0))
        self.assertEqual(expected_time_series.as_dict(file_name="don't care"),
                         time_series_dict)

    def test_c(self):
        """Test the setting of a single time series of an outgoing time series.

        """
        time_series = NegateSign(
            MockTimeSeries(('3201',     'discharge_drained', 10.0, 20.0, 30.0),
                           ('3201_PS1', 'Q',                  0.0,  1.0,  2.0)),
            outgoing_pumping_stations=['3201_PS1'])
        time_series_dict = time_series.as_dict(file_name="don't care")
        expected_time_series = \
            MockTimeSeries(('3201',     'discharge_drained', 10.0, 20.0, 30.0),
                           ('3201_PS1', 'Q',                  0.0, -1.0, -2.0))
        self.assertEqual(expected_time_series.as_dict(file_name="don't care"),
                         time_series_dict)


class Filter_as_dict_TestSuite(TestCase):

    def create_time_series(self, *parameters):
        args = [('3201', parameter, 0.0, 1.0, 2.0) for parameter in parameters]
        return MockTimeSeries(*args)

    def test_a(self):
        """Test the removal of a single time series when there are no relevant
        parameters.

        """
        time_series = Filter(
            self.create_time_series('discharge_flow_off'),
            relevant_parameters=[])
        time_series_dict = time_series.as_dict(file_name="don't care")
        self.assertEqual(0, len(time_series_dict))

    def test_b(self):
        """Test the removal of all time series when there are no relevant
        parameters.

        """
        time_series = Filter(
            self.create_time_series('discharge_flow_off', 'discharge_hardened'),
            relevant_parameters=[])
        time_series_dict = time_series.as_dict(file_name="don't care")
        self.assertEqual(0, len(time_series_dict))

    def test_c(self):
        """Test the removal of a single time series."""
        time_series = Filter(
            self.create_time_series('discharge_flow_off', 'discharge_hardened'),
            relevant_parameters=['discharge_hardened'])
        time_series_dict = time_series.as_dict(file_name="don't care")
        self.assertEqual(1, len(time_series_dict))
        self.assertEqual(create_time_series(0.0, 1.0, 2.0),
                         time_series_dict[('3201', 'discharge_hardened')])
