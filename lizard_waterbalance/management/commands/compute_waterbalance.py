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

from datetime import datetime
from os.path import join

from django.core.management.base import BaseCommand

from lizard_waterbalance.compute import WaterbalanceComputer
from lizard_waterbalance.models import WaterbalanceArea
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
    args = "<test-data-directory WaterbalanceArea-name start-date end-date>"
    help = "Calculates the water balance on the first open water."

    def handle(self, *args, **options):
        directory = args[0]
        area_name = args[1]
        start_date = datetime.strptime(args[2], "%Y-%m-%d")
        end_date = datetime.strptime(args[3], "%Y-%m-%d")

        # open_water = OpenWater.objects.all()[0]
        # buckets = [Bucket.objects.filter(name="landelijk")[0],
        #            Bucket.objects.filter(name="stedelijk")[0],
        #            Bucket.objects.filter(name="verhard")[0]]
        # bucket_computers = dict([(Bucket.UNDRAINED_SURFACE, compute_timeseries),
        #                          (Bucket.HARDENED_SURFACE, compute_timeseries_on_hardened_surface)])
        # pumping_stations = []

        timeseries_retriever = TimeseriesRetriever()
        timeseries_retriever.read_timeseries(join(directory, "timeserie.csv"))

        area = WaterbalanceArea.objects.filter(name=area_name)[0]
        assert not area is None

        area.retrieve_precipitation = lambda s,e: timeseries_retriever.get_timeseries("precipitation")
        area.retrieve_evaporation = lambda s,e: timeseries_retriever.get_timeseries("evaporation")
        area.retrieve_seepage = lambda s,e: timeseries_retriever.get_timeseries("seepage")

        assert not area.open_water is None

        area.open_water.retrieve_minimum_level = lambda : timeseries_retriever.get_timeseries("minimum level")
        area.open_water.retrieve_maximum_level = lambda : timeseries_retriever.get_timeseries("maximum level")

        waterbalance_computer = WaterbalanceComputer()
        bucket2outcome, level_control = \
                        waterbalance_computer.compute(area, start_date, end_date)

        f = open(join(directory, "intermediate-results.csv"), "w")
        for bucket, outcome in bucket2outcome.items():
            self.write_timeseries(f, bucket.name, "afstroming", outcome.flow_off)
            (drainage_timeseries, timeseries) = split_timeseries(outcome.net_drainage)
            self.write_timeseries(f, bucket.name, "drainage", drainage_timeseries)
            self.write_timeseries(f, bucket.name, "intrek", timeseries)
            self.write_timeseries(f, bucket.name, "kwel", outcome.seepage)
        self.write_timeseries(f, "openwater", "inlaat", level_control[0])
        self.write_timeseries(f, "openwater", "Pieter Post", level_control[1])
        f.close()

        # f = open(join(directory, "outcome.csv"), "w")
        # for key, outcome in result.items():
        #     for name, timeseries in outcome.name2timeseries().items():
        #         name = name2name[name]
        #         if name == "berging" or name == "netto neerslag":
        #             continue
        #         if name == "netto drainage":
        #             (drainage_timeseries, timeseries) = split_timeseries(timeseries)
        #             self.write_timeseries(f, key, "drainage", drainage_timeseries)
        #             name = "intrek"
        #         self.write_timeseries(f, key, name, timeseries)
        # f.close()

    def write_timeseries(self, file, key, name, timeseries):
        for (date, value) in timeseries.monthly_events():
            file.write("%s,%s,%d,%d,%d,%f\n" % (key, name, date.year,
                                                date.month, date.day, value))



