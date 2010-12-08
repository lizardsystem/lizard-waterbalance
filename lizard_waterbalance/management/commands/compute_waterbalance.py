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
# Initial date:       2010-12-07
#
#******************************************************************************

from os.path import join

from django.core.management.base import BaseCommand

from lizard_waterbalance.compute import compute_timeseries
from lizard_waterbalance.compute import open_water_compute
from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.timeseriesretriever import TimeseriesRetriever
from lizard_waterbalance.timeseriesstub import split_timeseries

name2name = dict([("evaporation", "verdamping"),
                  ("flow_off", "afstroming"),
                  ("net_drainage" , "netto drainage"),
                  ("net_precipitation" , "netto neerslag"),
                  ("precipitation", "neerslag"),
                  ("seepage", "kwel"),
                  ("storage", "berging")])

class Command(BaseCommand):
    args = "directory that contains test data"
    help = "Calculates the water balance on the first open water."

    def handle(self, *args, **options):
        directory = args[0]
        open_water = OpenWater.objects.all()[0]
        buckets = [Bucket.objects.all()[0]]
        bucket_computers = dict([(Bucket.UNDRAINED_SURFACE, compute_timeseries)])
        pumping_stations = []
        timeseries_retriever = TimeseriesRetriever()
        timeseries_retriever.read_timeseries(join(directory, "timeserie.csv"))
        result = open_water_compute(open_water, buckets, bucket_computers,
                                    pumping_stations, timeseries_retriever)
        f = open(join(directory, "outcome.csv"), "w")
        for key, outcome in result.items():
            for name, timeseries in outcome.name2timeseries().items():
                name = name2name[name]
                if name == "berging" or name == "netto neerslag":
                    continue
                if name == "netto drainage":
                    (drainage_timeseries, timeseries) = split_timeseries(timeseries)
                    self.write_timeseries(f, key, "drainage", drainage_timeseries)
                    name = "intrek"
                self.write_timeseries(f, key, name, timeseries)
        f.close()

    def write_timeseries(self, file, key, name, timeseries):
        for (date, value) in timeseries.monthly_events():
            file.write("%s,%s,%d,%d,%d,%f\n" % (key, name, date.year,
                                                date.month, date.day, value))



