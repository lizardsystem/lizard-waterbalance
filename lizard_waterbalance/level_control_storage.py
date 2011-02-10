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


class LevelControlAssignment:

    def compute(self, level_control, pumping_stations):
        """Computes and returns the computed level control time series.

        Parameters:
        * level_control -- pair of (total incoming, total outgoing) time series
        * pumping_stations -- list of PumpingStation(s) to handle the water flow

        The total incoming and total outgoing level control volumes have to be
        assigned to the intakes and pumps that can be used for level control. This
        method computes that assignment and returns it as a dictionary of
        PumpingStation to TimeseriesStub.

        The keys of the returned dictionary are the intakes and pumps that can
        be used for level control. The associated value is the level control
        time series.

        """
        assignment = {}
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

            assignment[pumping_station] = timeseries

        return assignment

class LevelControlStorage:
    """Implements the storage of a level control assignment to the database.

    Instance variables:
    * store_timeserie -- function used to store a level control time series

    """
    def __init__(self, store_timeserie=store_waterbalance_timeserie):
        """Set the function used to store a level control time series.

        Parameter:
        * store_timeserie -- function used to store a level control time series

        """
        self.store_timeserie = store_timeserie

    def store(self, pumping_stations, assignment):
        """Store the given level control assignment to the database.

        Parameter:
        * pumping_stations -- list of all PumpingStation's
        * assignment -- dictionary of PumpingStation to TimeseriesStub

        If a PumpingStation has a level control time series but should not be
        used for level control, this method deletes that level control time
        series.

        """
        for pumping_station in pumping_stations:
            try:
                timeseries = assignment[pumping_station]
                self.store_timeserie(pumping_station, "level_control", timeseries)
                pumping_station.save()
            except KeyError:
                waterbalance_timeserie = pumping_station.level_control
                if not waterbalance_timeserie is None:
                    pumping_station.level_control = None
                    pumping_station.save()
                    waterbalance_timeserie.delete()
