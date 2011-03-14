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

import logging
import itertools

from datetime import datetime
from datetime import timedelta
from math import fabs

from filereader import FileReader


def _first_of_day(event):
    """Return the first moment of the day for an event."""
    date, value = event
    return datetime(date.year, date.month, date.day)


def _first_of_month(event):
    """Return the first day of the month for an event."""
    date, value = event
    return datetime(date.year, date.month, 1)


def _first_of_quarter(event):
    """Return the first day of the quarter for an event.

    The first day of a quarter is returned:

      >>> dt = datetime(1972, 12, 25)
      >>> _first_of_quarter((dt, 'reinout'))
      datetime.datetime(1972, 10, 1, 0, 0)

      >>> dt = datetime(1972, 10, 1)
      >>> _first_of_quarter((dt, 'bla'))
      datetime.datetime(1972, 10, 1, 0, 0)

      >>> dt = datetime(1976, 01, 27)
      >>> _first_of_quarter((dt, 'maurits'))
      datetime.datetime(1976, 1, 1, 0, 0)

    """
    date, value = event
    month = 1 + ((date.month -1) / 3 * 3)
    return datetime(date.year, month, 1)


def _first_of_year(event):
    """Return the first day of the year for an event."""
    date, value = event
    return datetime(date.year, 1, 1)


def grouped_event_values(timeseries, period, average=False):
    """Return iterator with totals for days/months/years for timeseries."""
    groupers = {'year': _first_of_year,
                'month': _first_of_month,
                'quarter': _first_of_quarter,
                'day': _first_of_day}
    grouper = groupers.get(period)
    assert grouper is not None

    for date, events in itertools.groupby(timeseries.events(), grouper):
        if average:
            # To be able to count the events, we make a list of the generated
            # elements. There are ways to count them without having to make the list
            # explicit but this is the easy way.
            events = list(events)
            result = sum(value for (date, value) in events) / (1.0 * len(events))
        else:
            result = sum(value for (date, value) in events)
        yield date, result


def monthly_events(timeseries):
    """Return a generator to iterate over all monthly events.

    A TimeseriesStub stores daily events. This generator aggregates these
    daily events to monthly events. Each monthly events takes place on the
    first of the month and its value is the total value of the daily events
    for that month.

    """
    return grouped_event_values(timeseries, 'month')


def average_monthly_events(timeseries):
    """Return a generator to iterate over all average monthly events.

    A TimeseriesStub stores daily events. This generator aggregates these
    daily events to monthly events that is placed at the first of the month
    and whose value is the average value of the daily events for that month.

    """
    return grouped_event_values(timeseries, 'month', average=True)


class TimeseriesStub:
    """Represents a time series.

    A time series is a sequence of values ordered by date and time.

    Instance variables:
    * initial_value -- value on any date before the first date
    * events -- list of (date and time, value) tuples ordered by date and time

    """
    def __init__(self, *events):
        if len(events) == 0:
            events = []
        self._events = events

    def get_value(self, date_time):
        """Return the value on the given date and time.

        Note that this method assumes that the events are ordered earliest date
        and time first.

        """
        result = 0.0
        events = (event for event in self._events if event[0] >= date_time)
        event = next(events, None)
        if not event is None:
            if event[0] == date_time:
                result = event[1]
        return result

    def add_value(self, date_time, value):
        """Add the given value for the given date and time.

        Please note that events should be added earliest date and time first.

        """
        self._events.append((date_time, value))

    def raw_events(self):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function does not
        fill in the missing dates with value.

        """
        for date, value in self._events:
            yield date, value

    def events(self):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates with value 0.

        """
        date_to_yield = None # we initialize this variable to silence pyflakes
        for date, value in self._events:
            if not date_to_yield is None:
                while date_to_yield < date:
                    yield date_to_yield, 0
                    date_to_yield = date_to_yield + timedelta(1)
            yield date, value
            date_to_yield = date + timedelta(1)

    def monthly_events(self):
        """Return a generator to iterate over all monthly events.

        A TimeseriesStub stores daily events. This generator aggregates these
        daily events to monthly events. Each monthly events takes place on the
        first of the month and its value is the total value of the daily events
        for that month.

        """
        return grouped_event_values(self, 'month')

    def __eq__(self, other):
        """Return True iff the two given time series represent the same events."""
        my_events = list(self.events())
        your_events = list(other.events())
        equal = len(my_events) == len(your_events)
        if equal:
            for (my_event, your_event) in zip(my_events, your_events):
                equal = my_event[0] == your_event[0]
                if equal:
                    equal = fabs(my_event[1] - your_event[1]) < 1e-6
                if not equal:
                    break
        return equal


class TimeseriesWithMemoryStub(TimeseriesStub):

    def __init__(self, *args, **kwargs):
        TimeseriesStub.__init__(self, *args, **kwargs)

    def get_value(self, date_time):
        """Return the value on the given date and time.

        Note that this method assumes that the events are ordered earliest date
        and time first.

        """
        result = 0.0
        previous_event = None
        # note that we traverse the list of events in reverse
        for event in reversed(self._events):
            if event[0] < date_time:
                if previous_event is None:
                    result = event[1]
                else:
                    result = previous_event[1]
                break
            elif event[0] == date_time:
                result = event[1]
                previous_event = event
        return result

    def events(self):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates with the value on the latest known date.

        """
        date_to_yield = None # we initialize this variable to silence pyflakes
        previous_value = 0
        for date, value in self._events:
            if not date_to_yield is None:
                while date_to_yield < date:
                    yield date_to_yield, previous_value
                    date_to_yield = date_to_yield + timedelta(1)
            yield date, value
            previous_value = value
            date_to_yield = date + timedelta(1)


class TimeseriesRestrictedStub(TimeseriesStub):

    def __init__(self, *args, **kwargs):
        self.timeseries = kwargs["timeseries"]
        del kwargs["timeseries"]
        self.start_date = kwargs["start_date"]
        del kwargs["start_date"]
        self.end_date = kwargs["end_date"]
        del kwargs["end_date"]
        TimeseriesStub.__init__(self, *args, **kwargs)

    def events(self):
        for event in self.timeseries.events():
            if event[0] < self.start_date:
                continue
            if event[0] < self.end_date:
                yield event[0], event[1]
            else:
                break


def enumerate_events(*timeseries_list):
    """Yield the events for all the days of the given time series.

    Parameter:
      * timeseries_list *
        list of time series

    Each of the given time series should specify values for possibly
    non-continous ranges of dates. For each day present in a time series, this
    method yields a tuple of events of all time series. If that day is present
    in a time series, the tuple contains the corresponding event. If that day
    is not present, the tuple contains an event with value 0 at that day.

    The description above only mentions dates. However, this method can handle
    events whose 'date' include a time component *as long as* the 'date' object
    supports an isocalendar() method as datetime.date and datetime.datetime do.

    """
    next_start = datetime.max
    for timeseries in timeseries_list:
        start = next((event[0] for event in timeseries.events()), None)
        if not start is None:
            next_start = min(next_start, start)

    if next_start == datetime.max:
        # none of the time series contains an event and we stop immediately
        return

    # next_start is the first date for which an event is specified

    events_list = [timeseries.events() for timeseries in timeseries_list]
    earliest_event_list = [next(events, None) for events in events_list]

    timeseries_count = len(timeseries_list)

    no_events_are_present = False
    while not no_events_are_present:
        no_events_are_present = True
        to_yield = [(next_start, 0.0)] * timeseries_count
        for index, earliest_event in enumerate(earliest_event_list):
            if not earliest_event is None:
                no_events_are_present = False
                if earliest_event[0].isocalendar() == next_start.isocalendar():
                    to_yield[index] = earliest_event
                    earliest_event_list[index] = next(events_list[index], None)
        next_start = next_start + timedelta(1)
        if not no_events_are_present:
            yield tuple(to_yield)


def enumerate_merged_events(timeseries_a, timeseries_b):
    events_a = timeseries_a.events()
    events_b = timeseries_b.events()
    event_a = next(events_a, None)
    event_b = next(events_b, None)
    while not event_a is None and not event_b is None:
        if event_a[0].isocalendar() < event_b[0].isocalendar():
            yield event_a[0], event_a[1], 0
            event_a = next(events_a, None)
        elif event_a[0].isocalendar() > event_b[0].isocalendar():
            yield event_b[0], 0, event_b[1]
            event_b = next(events_b, None)
        else:
            yield event_a[0], event_a[1], event_b[1]
            event_a = next(events_a, None)
            event_b = next(events_b, None)
    if event_a is None:
        if not event_b is None:
            yield event_b[0], 0, event_b[1]
        for event in events_b:
            yield event[0], 0, event[1]
    else:
        if not event_a is None:
            yield event_a[0], event_a[1], 0
        for event in events_a:
            yield event[0], event[1], 0


def create_empty_timeseries(timeseries):
    """Return the empty TimeseriesStub that starts on the same day as the given time series.

    If the given time series is non-empty, this function returns a
    TimeseriesStub with a single event that starts on the day as the given time
    series and which has value 0.0. If the given time series is empty, this
    function returns an empty TimeseriesStub.

    """
    empty_timeseries = TimeseriesStub()
    event = next(timeseries.events(), None)
    if not event is None:
        empty_timeseries.add_value(event[0], 0.0)
    return empty_timeseries


def add_timeseries(timeseries_a, timeseries_b):
    """Return the TimeseriesStub that is the sum of the given time series."""
    result = TimeseriesStub()
    for date, value_a, value_b in enumerate_merged_events(timeseries_a, timeseries_b):
        result.add_value(date, value_a + value_b)
    return result


def subtract_timeseries(timeseries_a, timeseries_b):
    """Return the TimeseriesStub that is the difference of the given time series."""
    result = TimeseriesStub()
    for date, value_a, value_b in enumerate_merged_events(timeseries_a, timeseries_b):
        result.add_value(date, value_a - value_b)
    return result


def multiply_timeseries(timeseries, value):
    """Return the the product of the given time series with the given value.

    The product is a TimeseriesStub.

    """
    product = TimeseriesStub()
    for event in timeseries.events():
        product.add_value(event[0], event[1] * value)
    return product


def split_timeseries(timeseries):
    """Return the 2-tuple of non-positive and non-negative time series.

    Paramaters:
    * timeseries -- time series that contains the events for the new 2 -tuple

    This function creates a 2-tuple of TimeseriesStub, where the first element
    contains all non-positive events (of the given time series) and the second
    element contains all non-negative events. The 2 resulting time series have
    events for the same dates as the given time series, but with value zero if
    the value at that date does not have the right sign.

    """
    non_pos_timeseries = TimeseriesStub()
    non_neg_timeseries = TimeseriesStub()
    for (date, value) in timeseries.events():
        if value > 0:
            non_pos_timeseries.add_value(date, 0)
            non_neg_timeseries.add_value(date, value)
        elif value < 0:
            non_pos_timeseries.add_value(date, value)
            non_neg_timeseries.add_value(date, 0)
        else:
            non_pos_timeseries.add_value(date, 0)
            non_neg_timeseries.add_value(date, 0)
    return (non_pos_timeseries, non_neg_timeseries)


def create_from_file(filename, filereader=FileReader()):
    """Return a dictionary from bucket and open water name to bucket and open water outcome."""
    result = {}
    filereader.open(filename)
    for line in filereader.readlines():
        name, label, year, month, day, value = line.split(',')
        date = datetime(int(year), int(month), int(day))
        value = float(value)
        result.setdefault(name, {})
        result[name].setdefault(label, TimeseriesStub())
        result[name][label].add_value(date, value)
    filereader.close()
    return result
