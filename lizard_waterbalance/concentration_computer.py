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
from datetime import timedelta
from random import randrange

from lizard_waterbalance.timeseriesstub import enumerate_events
from lizard_waterbalance.timeseriesstub import split_timeseries
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class ConcentrationComputer:

    def compute(self, timeseries_list, concentration_list):
        """Compute and return the concentration time series.

        Parameters:
        * timeseries_list -- list of volume timeseries in [m3/day]
        * concentration_list -- list of concentration values in [mg/l]

        With respect to the input, concentration_list[i] specifies the amount
        of substance per m3 that occurs in timeseries_list[i]. This method sums
        these amounts for each day and returns the resulting timeseries.
        """
        timeseries = TimeseriesStub()
        for event_tuple in enumerate_events(*timeseries_list):
            date = event_tuple[0][0]
            value = sum((event[1] * concentration for event, concentration in
                         zip(event_tuple, concentration_list)))
            timeseries.add_value(date, value * 1000)
        return timeseries
