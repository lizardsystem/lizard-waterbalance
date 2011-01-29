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

from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import TimeseriesEvent
from lizard_waterbalance.models import WaterbalanceTimeserie

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

def store_waterbalance_timeserie(model, attribute_name, timeseries):
    """Store the given volume timeserie in the database.

    model is a Model with an attribute named attribute_name that refers to the
    ForeignKey of a WaterbalanceTimeserie. This function stores the given time
    series to the volume field of that WaterbalanceTimeserie.

    If the aforementioned WaterbalanceTimeserie is None, this function creates
    one. If the volume field of an already existing WaterbalanceTimeserie
    already contains a Timeseries, this function deletes it.

    """
    waterbalance_timeserie = model.__getattribute__(attribute_name)
    if  waterbalance_timeserie is None:
        waterbalance_timeserie = WaterbalanceTimeserie()
        waterbalance_timeserie.save()
        model.__setattr__(attribute_name, waterbalance_timeserie)
    previous_timeseries = waterbalance_timeserie.volume
    waterbalance_timeserie.volume = store(timeseries)
    waterbalance_timeserie.save()
    if not previous_timeseries is None:
        previous_timeseries.delete()

