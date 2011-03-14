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

from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.timeseriesretriever import TimeseriesRetriever
from lizard_waterbalance.timeseries import store_waterbalance_timeserie
from timeseries.timeseriesstub import TimeseriesStub


class Command(BaseCommand):
    args = "<test-data-directory open_water-name water-level-name timeseries-name>"
    help = "Imports the timeseries of the given water level."

    def handle(self, *args, **options):
        directory = args[0]
        area_slug = args[1]
        water_level_name = args[2]

        filename = join(directory, "timeserie.csv")
        timeseries_retriever = TimeseriesRetriever()
        timeseries_retriever.read_timeseries(filename)

        area = WaterbalanceArea.objects.get(slug__iexact=area_slug)
        open_water = area.open_water
        if water_level_name == "ondergrens":
            field_name = "minimum_level"
            timeseries_name = "minimum level"
        elif water_level_name == "bovengrens":
            field_name = "maximum_level"
            timeseries_name = "maximum level"
        elif water_level_name == "streefpeil":
            field_name = "target_level"
            timeseries_name = "target level"

        timeseries = TimeseriesStub()
        for date, value in timeseries_retriever.get_timeseries(timeseries_name).raw_events():
            timeseries.add_value(date, value)

        store_waterbalance_timeserie(open_water, field_name, timeseries, raw=True)

        timeserie = open_water.__getattribute__(field_name)
        name = "%s %s" % (water_level_name, open_water.name)
        timeserie.volume.name = name
        timeserie.volume.save()
        timeserie.name = name
        timeserie.save()
        open_water.save()


