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
#
#******************************************************************************

from datetime import datetime
from os.path import join

from django.core.management.base import BaseCommand

from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.timeseriesretriever import TimeseriesRetriever
from lizard_waterbalance.timeseries import store_waterbalance_timeserie
from lizard_waterbalance.timeseriesstub import TimeseriesStub


class Command(BaseCommand):
    args = "<test-data-directory pump-line-name timeseries-name>"
    help = "Imports the timeseries of the given pump line."

    def handle(self, *args, **options):
        directory = args[0]
        pump_line_name = args[1]
        timeseries_name = args[2]

        filename = join(directory, "timeserie.csv")
        timeseries_retriever = TimeseriesRetriever()
        timeseries_retriever.read_timeseries(filename)

        timeseries = TimeseriesStub()
        for date, value in timeseries_retriever.get_timeseries(timeseries_name).raw_events():
            timeseries.add_value(date, value)

        pump_line = PumpLine.objects.get(name__iexact=pump_line_name)
        store_waterbalance_timeserie(pump_line, "timeserie", timeseries, raw=True)
        name = "pomplijn %s" % pump_line_name
        pump_line.timeserie.volume.name = name
        pump_line.timeserie.volume.save()
        pump_line.timeserie.name = name
        pump_line.timeserie.save()
        pump_line.save()


