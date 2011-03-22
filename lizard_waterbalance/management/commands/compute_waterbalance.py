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
from optparse import make_option
from optparse import OptionParser
from os.path import join
import csv

from django.core.management.base import BaseCommand

from lizard_waterbalance.compute import WaterbalanceComputer
from lizard_waterbalance.compute import WaterbalanceComputer2
from lizard_waterbalance.models import WaterbalanceConf
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
    """Return a WaterbalanceConf and a WaterbalanceComputer for it

    The Waterbalancecomputer has some of its input data hard coded.

    Parameters:
    * area_slug -- slug of the area to create
    * start_date -- first day for which to retrieve events
    * end-date -- day after the last day for which to retrieve events
    * filename -- name of the file that contains the hard coded data

    """
    timeseries_retriever = TimeseriesRetriever()
    timeseries_retriever.read_timeseries(filename)

    configuration = WaterbalanceConf.objects.filter(slug=area_slug)[0]
    assert not configuration is None

    configuration.retrieve_precipitation = lambda s,e: retrieve_timeseries(timeseries_retriever, "precipitation", start_date, end_date)
    configuration.retrieve_evaporation = lambda s,e: retrieve_timeseries(timeseries_retriever, "evaporation", start_date, end_date)
    configuration.retrieve_seepage = lambda s,e: retrieve_timeseries(timeseries_retriever, "seepage", start_date, end_date)

    assert not configuration.open_water is None

    waterbalance_computer = WaterbalanceComputer(store_timeserie=lambda m, n, t: None)

    return configuration, waterbalance_computer


def export_table(configuration_slug, start_date, end_date, directory, input_directory):


    configuration = WaterbalanceConf.objects.filter(slug=configuration_slug)[0]

    waterbalance_computer = WaterbalanceComputer2(configuration)

    #tests
    input_ts = waterbalance_computer.get_input_timeseries(start_date, end_date)

    buckets = waterbalance_computer.get_buckets_timeseries(start_date, end_date)

    #step 3. Summarize according to labels
    buckets_summary = waterbalance_computer.get_bucketflow_summary(start_date, end_date)

    #step 4. Get vertical timeseries
    vertical_openwater = waterbalance_computer.get_vertical_open_water_timeseries(start_date, end_date)

    #step 5. Get level control
    level_control = waterbalance_computer.get_level_control_timeseries(start_date, end_date)

    #step 6. Get sluice_error
    reference_timeseries = waterbalance_computer.get_reference_timeseries(start_date, end_date)
    #sluice_error = waterbalance_computer.get_sluice_error_timeseries(start_date, end_date)

    #step 7. Get fractions
    fractions = waterbalance_computer.get_fraction_timeseries(start_date, end_date)

    buckets_summary = {"undrained": buckets_summary.undrained,
                       "drained": buckets_summary.drained,
                       "hardened": buckets_summary.hardened,
                       "flow_off": buckets_summary.flow_off,
                       "indraft": buckets_summary.indraft,
                       "totals":buckets_summary.totals}

    f = open(join(directory, "bastiaan-bucketoutcome.csv"), "w")
    csvf = csv.writer(f)

    #combine cols of table
    header = ['year', 'month', 'day']
    data_cols = []

    header+= ['input - precipitation', 'input - evaporation', 'input - seepage']
    data_cols.extend([input_ts['precipitation'], input_ts['evaporation'], input_ts['seepage']])

    for bucket, outcome in buckets.iteritems():
        header.append(bucket.name + ' kwel')
        data_cols.append(outcome.seepage)
        header.append(bucket.name + ' netto neerslag')
        data_cols.append(outcome.net_precipitation)
        header.append(bucket.name + ' afstroming')
        data_cols.append(outcome.flow_off)
        header.append(bucket.name + ' drainage')
        data_cols.append(outcome.net_drainage)
        header.append(bucket.name + ' storage upper bucket')
        data_cols.append(outcome.storage)

    for name, outcome in buckets_summary.iteritems():
        header.append('summary ' + name)
        data_cols.append(outcome)

    csvf.writerow(header)

    for event_tuple in enumerate_events(*data_cols):
        row = []
        date = event_tuple[0][0]
        row.extend([date.year, date.month, date.day])
        row.extend([event[1] for event in event_tuple])
        csvf.writerow(row)

    f.close()

    f = open(join(directory, "bastiaan-owbalanceoutcome.csv"), "w")
    csvf = csv.writer(f)

    #combine cols of table
    header = ['year', 'month', 'day']
    data_cols = []

    header+= ['bound - precipitation', 'bound - evaporation', 'bound - seepage']
    data_cols.extend([input_ts['precipitation'], input_ts['evaporation'], input_ts['seepage']])

    for name, outcome in buckets_summary.iteritems():
        header.append('bucket_summary ' + name)
        data_cols.append(outcome)

    for name, outcome in vertical_openwater.iteritems():
        header.append('ow ' + name)
        data_cols.append(outcome)

    for name, timeserie in input_ts['outgoing_timeseries'].iteritems():
        header.append('fixed_out ' + str(name))
        data_cols.append(timeserie)

    for name, timeserie in input_ts['incoming_timeseries'].iteritems():
        header.append('fixed_in ' + str(name))
        data_cols.append(timeserie)

    header.append('peilh_in')
    data_cols.append(level_control['level_control']['intake_time_series'])

    header.append('peilh_uit')
    data_cols.append(level_control['level_control']['pump_time_series'])

    for name, timeserie in level_control['open_water_cnt'].iteritems():
        header.append('ow_result ' + name)
        data_cols.append(timeserie)

    csvf.writerow(header)

    for event_tuple in enumerate_events(*data_cols):
        row = []
        date = event_tuple[0][0]
        row.extend([date.year, date.month, date.day])
        row.extend([event[1] for event in event_tuple])
        csvf.writerow(row)

    f.close()


class Command(BaseCommand):
    args = "test-data-directory WaterbalanceArea-name start-date end-date"
    help = "Calculates the water balance on the first open water."

    option_list = BaseCommand.option_list + (
        make_option("--multiple",
                    action = "store_false",
                    dest="export_table",
                    default=True,
                    help="store the results in multiple CSV files"),)

    def handle(self, *args, **options):

        parser = OptionParser(option_list=self.option_list)
        (options, args) = parser.parse_args()

        directory = args[1]
        area_slug = args[2]
        start_date = datetime.strptime(args[3], "%Y-%m-%d")
        end_date = datetime.strptime(args[4], "%Y-%m-%d")

        if options.export_table:
            export_table(area_slug, start_date, end_date, directory, directory)
        else:
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
