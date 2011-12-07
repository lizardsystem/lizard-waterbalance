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

from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import split_timeseries
from timeseries.timeseriesstub import SparseTimeseriesStub

logger = logging.getLogger(__name__)


class VerticalTimeseriesComputer:
    """Implements the computation of the vertical time series of an open water.

    The vertical time series of an open water are the precipitation,
    evaporation, seepage and infiltation time series.

    """

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

    def compute(self, surface, crop_evaporation_factor, precipitation,
                evaporation, seepage, infiltration):
        """Compute and return the vertical time series for the given surface as dictionary.

        The incoming time series precipitation and evaporation always contain
        non-negative event values although precipitation adds volume to the
        open water and evaporation removes volume. The incoming time series
        seepage can contain both positive and negative event values.

        This method returns the vertical time series as the list of time series
        [precipitation, evaporation, seepage, infiltation], where each time
        series is specified in [m3/day].

        The returned timeseries for precipitation and seepage only contain
        non-negative event values as they add volume to the open water. The
        returned timeseries for evaporation and infiltration only contain
        non-positive event values as they remove volume.

        Parameters:
        * surface -- surface in [m2]
        * crop_evaporation factor -- factor to multiply with the evaporation
        * precipitation -- precipitation time series in [mm/day]
        * evaporation -- evaporation time series in [mm/day]
        * seepage -- seepage time series in [mm/day]
        * infiltration -- seepage time series in [mm/day]

        """
        vertical_timeseries_list = [SparseTimeseriesStub(),
                                    SparseTimeseriesStub(),
                                    SparseTimeseriesStub(),
                                    SparseTimeseriesStub()]
        timeseries_list = [precipitation, evaporation, seepage, infiltration]
        index_evaporation = 1
        for event_tuple in enumerate_events(*timeseries_list):
            date = event_tuple[0][0]
            if self.inside_range(date) < 0:
                continue
            elif self.inside_range(date) > 0:
                break

            for index in range(0, len(timeseries_list)):
                value = event_tuple[index][1] * surface * 0.001
                if index == index_evaporation:
                    value = value * crop_evaporation_factor
                    if value > 0:
                        value = -value
                vertical_timeseries_list[index].add_value(date, value)

        return {"precipitation":vertical_timeseries_list[0],
                "evaporation":vertical_timeseries_list[1],
                "seepage":vertical_timeseries_list[2],
                "infiltration":vertical_timeseries_list[3]}

