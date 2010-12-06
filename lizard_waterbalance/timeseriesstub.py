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
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Pieter Swinkels
# Initial date:       2010-11-24
#
#******************************************************************************

from datetime import timedelta

class TimeseriesStub:
    """Represents a time series.

    A time series is a sequence of values ordered by date and time.

    Instance variables:
    * initial_value -- value on any date before the first date
    * events -- list of (date and time, value) tuples ordered by date and time

    """
    def __init__(self, initial_value):
        self.initial_value = initial_value
        self._events = []

    def get_value(self, date_time):
        """Return the value on the given date and time.

        Note that this method assumes that the events are ordered earliest date
        and time first.

        """
        values = (event[1] for event in self._events if date_time >= event[0])
        return next(values, self.initial_value)

    def add_value(self, date_time, value):
        """Add the given value for the given date and time.

        Please note that events should be added earliest date and time first.

        """
        self._events.append((date_time, value))

    def events(self):
        """Return a generator to iterate over all events.

        The generator iterates over the events in the order they were added.

        """
        previous_value = None
        date_to_yield = None # we initialize this variable to silence pyflakes
        for event in self._events:
            if previous_value:
                while date_to_yield < event[0]:
                    yield (date_to_yield, previous_value)
                    date_to_yield = date_to_yield + timedelta(1)
            yield event
            previous_value = event[1]
            date_to_yield = event[0] + timedelta(1)

def add_timeseries(timeseries_a, timeseries_b):
    """Return the sum of the given time series."""
    return ((a[0], a[1] + b[1]) for (a, b) in zip(timeseries_a.events(), timeseries_b.events()))

def multiply_timeseries(timeseries, value):
    """Return the product of the given time series with the given value."""
    return ((event[0], event[1] * value) for event in timeseries.events())
