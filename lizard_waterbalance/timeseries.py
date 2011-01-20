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

from django.utils.translation import ugettext as _

from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import TimeseriesEvent

def store(timeseries):
    """Stores and returns the given time series as a Timeseries.

    Parameters:
    * timeseries -- time series that supports the events() method

    """
    db_timeseries = Timeseries()
    db_timeseries.save()
    for event in timeseries.events():
        db_timeseries_event = TimeseriesEvent()
        db_timeseries_event.timeseries = db_timeseries
        db_timeseries_event.time = event[0]
        db_timeseries_event.value = event[1]
        db_timeseries_event.save()
    return db_timeseries

