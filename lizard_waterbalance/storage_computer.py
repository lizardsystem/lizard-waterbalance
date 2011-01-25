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
# Initial date:       2011-01-25
#
#******************************************************************************

from lizard_waterbalance.timeseriesstub import enumerate_events
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class StorageComputer:

    def compute(self, surface, init_water_level, buckets_summary,
                intakes_timeseries, pumps_timeseries, precipitation,
                evaporation, seepage):
        """Return the computed storage time series for the given surface.

        Parameters:
        * surface -- surface of the open water in [m2]
        * init_water_level -- initial water level in [m]
        * buckets_summary -- BucketsSummary with the summed buckets outcome
        * intakes_timeseries -- list of intake timeseries in [m3/day]
        * pumps_timeseries -- list of pump timeseries in [m3/day]
        * precipitation -- precipitation time series in [mm/day]
        * evaporation -- evaporation time series in [mm/day]
        * seepage -- seepage time series in [mm/day]

        """

        storage_timeseries = TimeseriesStub()
        storage = surface * init_water_level
        timeseries_list = []
        timeseries_list += [buckets_summary.hardened]
        timeseries_list += [buckets_summary.drained]
        timeseries_list += [buckets_summary.undrained]
        timeseries_list += [buckets_summary.flow_off]
        timeseries_list += [buckets_summary.infiltration]
        timeseries_list += intakes_timeseries[:]
        timeseries_list += pumps_timeseries[:]
        timeseries_list += [precipitation, evaporation, seepage]
        for event_tuple in enumerate_events(*timeseries_list):
            storage += sum((event[1] for event in event_tuple[0:5]))
            for intake_event in event_tuple[5:-3-len(pumps_timeseries)]:
                storage += intake_event[1]
            for pump_event in event_tuple[-3-len(pumps_timeseries):-3]:
                storage -= pump_event[1]
            precipitation_event, evaporation_event, seepage_event = event_tuple[-3], event_tuple[-2], event_tuple[-1]
            date = precipitation_event[0]
            storage += surface * (precipitation_event[1] - evaporation_event[1] + seepage_event[1]) * 0.001
            storage_timeseries.add_value(date, storage)
        return storage_timeseries


