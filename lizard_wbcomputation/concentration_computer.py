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
# Copyright 2011, 2012 Nelen & Schuurmans
#
#******************************************************************************

from datetime import datetime
import logging

from timeseries.timeseriesstub import enumerate_dict_events
from timeseries.timeseriesstub import enumerate_events
from timeseries.timeseriesstub import SparseTimeseriesStub

logger = logging.getLogger(__name__)

# class ConcentrationComputer:

#     def compute(self,
#                 fractions_dict, concentration_dict,
#                 start_date, end_date):
#         """Compute and return the concentration time series.

#         Parameters:
#         * fractions_list -- dict of fractions timeseries in [0.0, 1.0]
#         * concentration_list -- dict of label keys with concentration values in [mg/l]

#         Computation is based on constant concentration of the fractions
#         """
#         timeseries = SparseTimeseriesStub()
#         for events in enumerate_dict_events(fractions_dict):
#             date = events['date']
#             del(events['date'])
#             concentration = 0
#             for key, value in events.items():
#                 if key in ['intakes', 'defined_input']:
#                     for key_intake, value_intake in value.items():
#                         if key_intake == 'intake_wl_control':
#                             concentration += value_intake[1] * concentration_dict[key_intake]
#                         else:
#                             concentration += value_intake[1] * concentration_dict[key_intake.label.program_name]
#                 else:
#                     concentration += value[1] * concentration_dict[key]

#             timeseries.add_value(date, concentration)

#         return timeseries

class ConcentrationComputer2:

    def compute(self,
                inflow_dict, outflow_dict, storage, concentration_dict,
                start_date, end_date):
        """Compute and return the concentration time series.

        Parameters:
          *inflow_dict*
            dictionary that maps the name of an incoming flow to either a time
            series or to a dictionary of PumpingStation to time series
          *inflow_dict*
            dictionary that maps the name of an outgoin flow to either a time
            series or to a dictionary of PumpingStation to time series
          *storage*
            storage time series
          *concentration_dict*
            dictionary that maps the name of an incoming flow to a
            concentration value

        Computation is based on constant concentration of the fractions
        """
        total_outflow = self._computeOutgoingVolume(outflow_dict)

        start_storage = next(storage.events(start_date, end_date))[1]
        storage_chloride = start_storage * concentration_dict['initial']

        delta = SparseTimeseriesStub()

        timeseries = SparseTimeseriesStub()
        for events in enumerate_dict_events(dict(tuple(inflow_dict.items()) + (('total_outflow', total_outflow), ('storage', storage)))):
            date = events['date']
            if date < start_date:
                continue
            if date >= end_date:
                break

            total_outflow = -events['total_outflow'][1]
            storage = events['storage'][1]
            del(events['date'])
            del(events['total_outflow'])
            del(events['storage'])

            out = (storage_chloride/storage) * total_outflow

            plus = 0.0
            for key, value in events.items():
                if key in ['intakes', 'defined_input', 'intake_wl_control']:
                    for key_intake, value_intake in value.items():
                        plus += value_intake[1] * concentration_dict[key_intake.label.program_name]
                else:
                    plus += value[1] * concentration_dict[key]
            storage_chloride = storage_chloride + plus - out
            timeseries.add_value(date, storage_chloride/storage)
            delta.add_value(date, plus - out)

        return timeseries, delta

    def _computeOutgoingVolume(self, outflow_dict):
        total_outflow = SparseTimeseriesStub()
        for events in enumerate_dict_events(outflow_dict):
            date = events['date']
            del(events['evaporation'])
            del(events['date'])
            total= 0.0
            for key, event in events.items():
                if key in ['outtakes', 'defined_output', 'outtake_wl_control']:
                    for key_outtake, event_outtake in event.items():
                        total += event_outtake[1]
                else:
                     total += event[1]
            total_outflow.add_value(date, total)
        return total_outflow

class ConcentrationComputer(object):

    def compute(self):
        concentration_timeseries = SparseTimeseriesStub()
        concentration = self.initial_concentration
        volume = self.initial_volume
        chloride = volume * concentration
        for events in enumerate_events(self.incoming_volume_timeseries,
                                       self.incoming_chloride_timeseries,
                                       self.outgoing_volume_timeseries):
            date = events[0][0]
            incoming_volume = events[0][1]
            outgoing_volume = events[2][1]
            incoming_chloride = events[1][1]

            chloride = ((volume + incoming_volume + outgoing_volume) / (volume + incoming_volume)) * (chloride + incoming_chloride)
            concentration = chloride / (volume + incoming_volume + outgoing_volume)
            volume += incoming_volume + outgoing_volume

            concentration_timeseries.add_value(date, concentration)
        return concentration_timeseries
