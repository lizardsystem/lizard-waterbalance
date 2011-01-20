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

from datetime import datetime
from unittest import TestCase

from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.timeseries import store
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class TimeseriesTests(TestCase):
    """Contains tests for the persistent storage of Timeseries.

    """
    def test_a(self):
        events = [(datetime(2011, 1, 20), 10.0), (datetime(2011, 1, 21), 11.0)]
        db_timeseries = store(TimeseriesStub(*events))
        queryset = Timeseries.objects.filter(pk__exact=db_timeseries.pk)
        self.assertEqual(1, queryset.count())
        db_events = list(queryset.get(pk=db_timeseries.pk).events())
        self.assertEqual(events, db_events)
