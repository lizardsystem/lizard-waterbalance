#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2011 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
#
#******************************************************************************

from datetime import datetime

from lizard_waterbalance.timeseriesstub import add_timeseries
from lizard_waterbalance.timeseriesstub import enumerate_events
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class SluiceErrorComputer:

    def compute(self, open_water, level_control, start_date, end_date):
        """Compute and return the sluice error.

        The sluice error on a specific day is defined as the sum of the computed
        intake and pump values minus the sum of the measured intake and pump
        values.

        This function returns the TimeseriesStub that contains the sluice error
        for each day in the given horizon.

        Parameters:
          * open_water *
            OpenWater for which to compute the level control
          * level_control *
            pair of TimeseriesStub(s) where the first contains the total
            computed discharges of level control intakes and the second the
            total computed discharges of level control pumps
          * start_date *
            the first date for which to compute the sluice error
          * end_date *
            the first date after the last date for which to compute the sluice
            error

        """
        sluice_error_timeseries = TimeseriesStub()
        self.open_water = open_water
        measured_timeseries = self._retrieve_measured_timeseries()
        computed_timeseries = self._retrieve_computed_timeseries(level_control)
        for events in enumerate_events(computed_timeseries, measured_timeseries):
            date = events[0][0]
            sluice_error_timeseries.add_value(date, events[0][1] - events[1][1])
        return sluice_error_timeseries

    def _retrieve_measured_timeseries(self):
        return self._retrieve_net_timeseries(only_input=False)

    def _retrieve_computed_timeseries(self, level_control):
        computed_timeseries = self._retrieve_net_timeseries(only_input=True)
        for timeseries in level_control:
            computed_timeseries = add_timeseries(computed_timeseries, timeseries)
        return computed_timeseries

    def _retrieve_net_timeseries(self, only_input):
        net_timeseries = TimeseriesStub()
        timeseries = self.open_water.retrieve_incoming_timeseries(only_input=only_input)
        timeseries += self.open_water.retrieve_outgoing_timeseries(only_input=only_input)
        for events in enumerate_events(*timeseries):
            date = events[0][0]
            net_timeseries.add_value(date, sum(e[1] for e in events))
        return net_timeseries
