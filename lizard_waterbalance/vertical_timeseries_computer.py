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

from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import split_timeseries
from timeseries.timeseriesstub import TimeseriesStub

class VerticalTimeseriesComputer:
    """Implements the computation of the vertical time series of an open water.

    The vertical time series of an open water are the precipitation,
    evaporation, seepage and infiltation time series.

    """

    def compute(self, surface, crop_evaporation_factor, precipitation,
                evaporation, seepage):
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
        returned timeseries for evaporation and infiltation only contain
        non-positive event values as they remove volume.

        Parameters:
        * surface -- surface in [m2]
        * crop_evaporation factor -- factor to multiply with the evaporation
        * precipitation -- precipitation time series in [mm/day]
        * evaporation -- evaporation time series in [mm/day]
        * seepage -- seepage time series in [mm/day]

        """
        vertical_timeseries_list = [TimeseriesStub(),
                                    TimeseriesStub(),
                                    TimeseriesStub(),
                                    TimeseriesStub()]
        timeseries_list = [precipitation, evaporation, seepage]
        index_evaporation = 1
        for event_tuple in enumerate_events(*timeseries_list):
            date = event_tuple[0][0]
            for index in range(0, len(timeseries_list)):
                value = event_tuple[index][1] * surface * 0.001
                if index == index_evaporation:
                    value = value * crop_evaporation_factor
                    if value > 0:
                        value = -value
                vertical_timeseries_list[index].add_value(date, value)
        vertical_timeseries_list[3], vertical_timeseries_list[2] = \
                                     split_timeseries(vertical_timeseries_list[2])
        return {"precipitation":vertical_timeseries_list[0],
                      "evaporation":vertical_timeseries_list[1],
                      "seepage":vertical_timeseries_list[2],
                      "infiltration":vertical_timeseries_list[3]}

