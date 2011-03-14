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

from lizard_waterbalance.compute import WaterbalanceComputer
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.timeseriesretriever import TimeseriesRetriever
from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import split_timeseries
from timeseries.timeseriesstub import TimeseriesStub

name2name = dict([("evaporation", "verdamping"),
                  ("flow_off", "afstroming"),
                  ("net_drainage" , "netto drainage"),
                  ("net_precipitation" , "netto neerslag"),
                  ("precipitation", "neerslag"),
                  ("seepage", "kwel"),
                  ("storage", "berging")])

def retrieve_timeseries(timeseries_retriever, name, start_date, end_date):
    timeseries = TimeseriesStub()
    for event in timeseries_retriever.get_timeseries(name).events():
        if event[0] < start_date:
            continue
        if event[0] < end_date:
            timeseries.add_value(event[0], event[1])
        else:
            break
    return timeseries

def create_waterbalance_computer(area_slug, start_date, end_date, filename):
    """Return a WaterbalanceArea and a WaterbalanceComputer for it

    The Waterbalancecomputer has some of its input data hard coded.

    Parameters:
    * area_slug -- slug of the area to create
    * start_date -- first day for which to retrieve events
    * end-date -- day after the last day for which to retrieve events
    * filename -- name of the file that contains the hard coded data

    """
    timeseries_retriever = TimeseriesRetriever()
    timeseries_retriever.read_timeseries(filename)

    area = WaterbalanceArea.objects.filter(slug=area_slug)[0]
    assert not area is None

    area.retrieve_precipitation = lambda s,e: retrieve_timeseries(timeseries_retriever, "precipitation", start_date, end_date)
    area.retrieve_evaporation = lambda s,e: retrieve_timeseries(timeseries_retriever, "evaporation", start_date, end_date)
    area.retrieve_seepage = lambda s,e: retrieve_timeseries(timeseries_retriever, "seepage", start_date, end_date)

    assert not area.open_water is None

    waterbalance_computer = WaterbalanceComputer(store_timeserie=lambda m, n, t: None)

    return area, waterbalance_computer

class Command(BaseCommand):
    args = "<test-data-directory WaterbalanceArea-name start-date end-date>"
    help = "Calculates the water balance on the first open water."

    def handle(self, *args, **options):
        directory = args[0]
        area_slug = args[1]
        start_date = datetime.strptime(args[2], "%Y-%m-%d")
        end_date = datetime.strptime(args[3], "%Y-%m-%d")

        filename = join(directory, "timeserie.csv")
        area, waterbalance_computer = create_waterbalance_computer(area_slug, start_date, end_date, filename)

        bucket2outcome, level_control, waterbalance_outcome = \
                        waterbalance_computer.compute(area, start_date, end_date)

        f = open(join(directory, "intermediate-results.csv"), "w")
        for bucket, outcome in bucket2outcome.items():
            self.write_timeseries(f, bucket.name, "afstroming", outcome.flow_off)
            (drainage_timeseries, timeseries) = split_timeseries(outcome.net_drainage)
            self.write_timeseries(f, bucket.name, "drainage", drainage_timeseries)
            self.write_timeseries(f, bucket.name, "intrek", timeseries)
            self.write_timeseries(f, bucket.name, "kwel", outcome.seepage)
            (evaporation_timeseries, timeseries) = split_timeseries(outcome.net_precipitation)
            self.write_timeseries(f, bucket.name, "verdamping", evaporation_timeseries)
            self.write_timeseries(f, bucket.name, "neerslag", timeseries)
        self.write_timeseries(f, "openwater", "inlaat peilbeheer", level_control[0])
        self.write_timeseries(f, "openwater", "pomp peilbeheer", level_control[1])
        f.close()

        f = open(join(directory, "Bastiaan-results.csv"), "w")
        f.write("bakje,jaar,maand,dag,berging,afstroming,netto drainage,kwel,netto neerslag\n")
        for bucket, outcome in bucket2outcome.items():
            for event_tuple in enumerate_events(outcome.storage,
                                                outcome.flow_off,
                                                outcome.net_drainage,
                                                outcome.seepage,
                                                outcome.net_precipitation):
                date = event_tuple[0][0]
                assert date == event_tuple[1][0]
                assert date == event_tuple[2][0]
                assert date == event_tuple[3][0]
                assert date == event_tuple[4][0]
                storage = event_tuple[0][1]
                flow_off = event_tuple[1][1]
                net_drainage = event_tuple[2][1]
                seepage = event_tuple[3][1]
                net_precipitation = event_tuple[4][1]
                f.write("%s,%d,%d,%d,%f,%f,%f,%f,%f\n" % (bucket.name, date.year, date.month, date.day, storage, flow_off, net_drainage, seepage, net_precipitation))
        f.close()

        f = open(join(directory, "waterbalance-outcome.csv"), "w")

        for key, timeseries in waterbalance_outcome.open_water_timeseries.iteritems():
            self.write_timeseries(f, "open water timeseries", key, timeseries)

        for key, timeseries in waterbalance_outcome.level_control_assignment.iteritems():
            self.write_timeseries(f, "level control assignment", key, timeseries)

        for key, timeseries in waterbalance_outcome.open_water_fractions.iteritems():
            self.write_timeseries(f, "open water fractions", key, timeseries)

        for key, timeseries in waterbalance_outcome.intake_fractions.iteritems():
            self.write_timeseries(f, "intake fractions", key, timeseries)

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
        for (date, value) in timeseries.events():
            file.write("%s,%s,%d,%d,%d,%f\n" % (key, name, date.year,
                                                date.month, date.day, value))



