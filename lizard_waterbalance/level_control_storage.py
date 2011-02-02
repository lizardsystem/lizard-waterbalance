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
# Initial date:       2011-01-26
#
#******************************************************************************

from lizard_waterbalance.timeseries import store_waterbalance_timeserie
from lizard_waterbalance.timeseriesstub import multiply_timeseries
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class LevelControlStorage:

    def store(self, level_control, pumping_stations):
        """Computes and stores the computed level control time series.

        Parameters:
        * level_control -- pair of (total incoming, total outgoing) time series
        * pumping_stations -- list of PumpingStation(s) to handle the water flow

        """
        (incoming_timeseries, outgoing_timeseries) = level_control
        for pumping_station in pumping_stations:
            timeseries = None

            fraction = pumping_station.percentage / 100.0
            if pumping_station.computed_level_control:
                if pumping_station.into:
                    timeseries = multiply_timeseries(incoming_timeseries, fraction)
                else:
                    timeseries = multiply_timeseries(outgoing_timeseries, fraction)

            if timeseries is None:
                if not pumping_station.level_control is None:
                    timeseries = TimeseriesStub()
            if timeseries is None:
                continue

            store_waterbalance_timeserie(pumping_station, "level_control", timeseries)
            pumping_station.save()
