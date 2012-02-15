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

from timeseries.timeseriesstub import enumerate_dict_events
from timeseries.timeseriesstub import SparseTimeseriesStub


class FractionComputer:

    def compute(self, area, buckets_summary, precipitation_timeseries, seepage_timeseries,
                storage_timeseries, total_output_timeseries, intakes_timeseries, start_date, end_date):
        """Compute and return the fraction series.

        This function returns the pair of SparseTimeseriesStub(s) that consists of
        the intake time series and pump time series for the given open water.

        Parameters:
        * area -- Area for which to compute the level control
        * buckets_summary -- BucketsSummary with the summed buckets outcome
        * precipitation,
        * seepage,
        * storage_timeseries -- storage time series in [m3/day]
        * intakes_timeseries -- list of intake timeseries in [m3/day]

        """
        fractions_initial = SparseTimeseriesStub()
        fractions_precipitation = SparseTimeseriesStub()
        fractions_seepage = SparseTimeseriesStub()
        fractions_hardened = SparseTimeseriesStub()
        fractions_sewer = SparseTimeseriesStub()
        fractions_drained = SparseTimeseriesStub()
        fractions_undrained = SparseTimeseriesStub()
        fractions_flow_off = SparseTimeseriesStub()
        fractions_intakes = {}
        for key in intakes_timeseries.keys():
            fractions_intakes[key] = SparseTimeseriesStub()

        previous_initial = 1.0
        previous_precipitation = 0.0
        previous_seepage = 0.0
        previous_hardened = 0.0
        previous_sewer = 0.0
        previous_drained = 0.0
        previous_undrained = 0.0
        previous_flow_off = 0.0
        previous_intakes = {}
        for key in intakes_timeseries.keys():
            previous_intakes[key] = 0.0

        previous_storage = self.initial_storage(area)

        ts = {}
        ts['hardened'] = buckets_summary.hardened
        ts['drained'] = buckets_summary.drained
        ts['undrained'] = buckets_summary.undrained
        ts['flow_off'] = buckets_summary.flow_off
        ts['precipitation'] = precipitation_timeseries
        ts['seepage'] = seepage_timeseries
        ts['sewer'] = buckets_summary.sewer
        ts['storage'] = storage_timeseries
        ts['total_output'] = total_output_timeseries
        ts['intakes'] = intakes_timeseries

        first = True
        for events in enumerate_dict_events(ts):
            date = events['date']
            if date < start_date:
                continue
            if date >= end_date:
                break

            if first:
                first = False
                previous_storage = (area.init_water_level - area.bottom_height) * area.surface


            total_output = -1 * events['total_output'][1]
            current_storage = events['storage'][1]

            initial = self.compute_fraction(0,
                                            total_output,
                                            current_storage,
                                            previous_initial,
                                            previous_storage)

            precipitation = self.compute_fraction(events['precipitation'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_precipitation,
                                                  previous_storage)
            seepage = self.compute_fraction(events['seepage'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_seepage,
                                                  previous_storage)

            hardened = self.compute_fraction(events['hardened'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_hardened,
                                                  previous_storage)

            sewer = self.compute_fraction(events['sewer'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_sewer,
                                                  previous_storage)

            drained = self.compute_fraction(events['drained'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_drained,
                                                  previous_storage)

            undrained = self.compute_fraction(events['undrained'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_undrained,
                                                  previous_storage)

            flow_off = self.compute_fraction(events['flow_off'][1],
                                                  total_output,
                                                  current_storage,
                                                  previous_flow_off,
                                                  previous_storage)
            intakes = {}
            for key, intake_timeserie in events['intakes'].items():
                    intakes[key] = self.compute_fraction(intake_timeserie[1],
                                                           total_output,
                                                           current_storage,
                                                           previous_intakes[key],
                                                           previous_storage)

            # total_fractions = initial + precipitation + seepage + sewer + hardened + \
            #                   drained + undrained + flow_off + sum(intakes.values())

            # print "total_fractions", total_fractions

            fractions_initial.add_value(date, initial)
            previous_initial = initial
            fractions_precipitation.add_value(date, precipitation)
            previous_precipitation = precipitation
            fractions_seepage.add_value(date, seepage)
            previous_seepage = seepage
            fractions_hardened.add_value(date, hardened)
            previous_hardened = hardened
            fractions_sewer.add_value(date, sewer)
            previous_sewer = sewer
            fractions_drained.add_value(date, drained)
            previous_drained = drained
            fractions_undrained.add_value(date, undrained)
            previous_undrained = undrained
            fractions_flow_off.add_value(date, flow_off)
            previous_flow_off = flow_off

            previous_intakes = {}
            for key in intakes.keys():
                fractions_intakes[key].add_value(date, intakes[key])
                previous_intakes[key] = intakes[key]

            previous_storage = current_storage

        result = {'initial':fractions_initial,
                'precipitation':fractions_precipitation,
                'seepage':fractions_seepage,
                'hardened':fractions_hardened,
                'drained':fractions_drained,
                'sewer':fractions_sewer,
                'undrained':fractions_undrained,
                'flow_off':fractions_flow_off,
                'intakes': {} }

        for key in intakes_timeseries.keys():
            result['intakes'][key] = fractions_intakes[key]

        return result

    def compute_fraction(self, current_input, current_total_output, current_storage, previous_fraction, previous_storage):

        input = current_input
        output = previous_fraction * current_total_output
        new_storage_fraction = previous_fraction * previous_storage + input - output
        fraction = new_storage_fraction / current_storage
        return fraction

    def initial_storage(self, area):
        return 1.0 * area.surface * \
               (area.init_water_level - area.bottom_height)

    def total_incoming(self, event_values):
        incoming_values = event_values[:]
        del incoming_values[self.index_storage]
        del incoming_values[self.index_indraft]
        return sum(incoming_values)

