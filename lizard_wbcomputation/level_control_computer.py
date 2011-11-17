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

import logging

from datetime import timedelta

from timeseries.timeseriesstub import enumerate_dict_events
from timeseries.timeseriesstub import SparseTimeseriesStub

logger = logging.getLogger(__name__)

class DateRange:

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def inside(self, date):
        if date < self.start_date:
            result = -1
        elif date < self.end_date:
            result = 0
        else:
            result = 1
        return result

class LevelControlComputer:

    def __init__(self, inside_range=lambda date: 0):
        """Set the function to determine if a date lies in a specific range.

        The level control only has to be computed for dates that lie in a
        specific range of dates. The given function should return a
          - negative number if the given date is before the start of the range,
          - positive number if the given date is at the end of the range or
            later, and
          - zero if the given date lies in the range.

        If the caller does not supply a function at the construction of a
        LevelControlComputer, the LevelControlComputer stores a function that
        considers every date to lie in the aforementioned range. However, the
        caller is free to override that function, which is referenced by
        self.inside_range, at a later time.

        """
        self.inside_range = inside_range

    def compute(self, area, buckets_summary, precipitation, evaporation, seepage, infiltration,
                minimum_level_timeseries, maximum_level_timeseries,
                intakes_timeseries, pumps_timeseries,
                max_intake = None, max_outtake = None):
        """Compute and return the pair of intake and pump time series.

        This function returns the pair of SparseTimeseriesStub(s) that consists of
        the intake time series and pump time series for the given open water.

        Parameters:
        * area -- Area for which to compute the level control
        * buckets_summary -- BucketsSummary with the summed buckets outcome
        * precipitation,
        * evaporation,
        * seepage,
        * infiltration
        * intakes_timeseries -- dict of intake timeseries in [m3/day]
        * pumps_timeseries -- dict of pump timeseries in [m3/day]

        """
        storage = SparseTimeseriesStub()
        result = SparseTimeseriesStub()
        water_level_timeseries = SparseTimeseriesStub()
        pump_time_series = SparseTimeseriesStub()
        intake_time_series = SparseTimeseriesStub()
        total_incoming = SparseTimeseriesStub()
        total_outgoing = SparseTimeseriesStub()

        surface = 1.0 * area.surface
        water_level = 0 #area.init_water_level

        ts = {}
        ts['bucket_total_incoming'] = buckets_summary.total_incoming
        ts['bucket_total_outgoing'] = buckets_summary.total_outgoing
        ts['precipitation'] = precipitation
        ts['evaporation'] = evaporation
        ts['seepage'] = seepage
        ts['infiltration'] = infiltration
        ts['min_level'] = minimum_level_timeseries
        ts['max_level'] = maximum_level_timeseries

        ts['intakes'] = {}
        for intake, timeseries in intakes_timeseries.iteritems():
            if not intake.computed_level_control:
                ts['intakes'][intake] = timeseries

        ts['pumps'] = {}
        for pump, timeseries in pumps_timeseries.iteritems():
            if not pump.computed_level_control:
                ts['pumps'][pump] = timeseries

        for events in enumerate_dict_events(ts):
            date = events['date']
            if self.inside_range(date) < 0:
                continue
            elif self.inside_range(date) > 0:
                break

            if not events.has_key('intakes'):
                events['intakes'] = {}

            incoming_value = [ events['bucket_total_outgoing'][1],
                                  events['precipitation'][1],
                                  events['seepage'][1]] + \
                                  [event[1] for event in events['intakes'].values()]

            incoming_value = sum(incoming_value)

            if not events.has_key('pumps'):
                events['pumps'] = {}

            outgoing_value = [ events['bucket_total_incoming'][1],
                                  events['infiltration'][1],
                                  events['evaporation'][1]] + \
                                  [event[1] for event in events['pumps'].values()]

            outgoing_value = sum(outgoing_value)

            water_level += (incoming_value + outgoing_value) / surface

            level_control = self._compute_level_control(surface, water_level, events['min_level'][1], events['max_level'][1])

            if level_control < 0:
                if max_outtake is not None:
                    pump = max(level_control, -1*max_outtake)
                else:
                    pump = level_control
                intake = 0
            else:
                pump = 0
                if max_intake is not None:
                    intake = min(level_control, max_intake)
                else:
                    intake = level_control

            water_level += (pump + intake) / surface

            pump_time_series.add_value(date, pump)
            intake_time_series.add_value(date, intake)

            water_level_timeseries.add_value(date, water_level)

            storage_value = (water_level - area.bottom_height) * surface
            storage.add_value(date, storage_value)

            result.add_value(date, level_control)

            total_incoming.add_value(date, sum([incoming_value, intake]))
            total_outgoing.add_value(date, sum([outgoing_value, pump]))

            date += timedelta(1)

        return {'intake_wl_control':intake_time_series,
                'outtake_wl_control':pump_time_series,
                'storage':storage,
                'water_level':water_level_timeseries,
                'total_incoming':total_incoming,
                'total_outgoing':total_outgoing}

    def _compute_level_control(self, surface, water_level, minimum_water_level, maximum_water_level):
        """Compute and return the level control for the given date.

        Parameters:
        * surface -- surface of the open water in [m2]
        * water_level -- uncorrected water level of the open water in [m]
        * minimum_water_level -- minimum allowed water level
        * maximum_water_level -- maximum allowed water level

        """
        if water_level > maximum_water_level:
            level_control = -(water_level - maximum_water_level) * surface
        elif water_level < minimum_water_level:
            level_control = (minimum_water_level - water_level) * surface
        else:
            level_control = 0
        return level_control
