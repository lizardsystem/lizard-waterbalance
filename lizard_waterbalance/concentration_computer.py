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
from datetime import timedelta
from random import randrange

from timeseries.timeseriesstub import enumerate_dict_events
from timeseries.timeseriesstub import split_timeseries
from timeseries.timeseriesstub import TimeseriesStub


class ConcentrationComputer:

    def compute(self, 
                fractions_dict, concentration_dict,
                start_date, end_date):
        """Compute and return the concentration time series.

        Parameters:
        * fractions_list -- dict of fractions timeseries in [0.0, 1.0]
        * concentration_list -- dict of label keys with concentration values in [mg/l]
        
        Computation is based on constant concentration of the fractions
        """
          
       
        timeseries = TimeseriesStub()
        for events in enumerate_dict_events(fractions_dict):
            date = events['date']
            del(events['date'])
            concentration = 0
            for key, value in events.items():
                if key in ['intakes', 'defined_input']:
                    for key_intake, value_intake in value.items():
                        if key_intake == 'intake_wl_control':
                            concentration += value_intake[1] * concentration_dict[key_intake]
                        else:
                            concentration += value_intake[1] * concentration_dict[key_intake.label.program_name]
                else:
                    concentration += value[1] * concentration_dict[key]
            
            timeseries.add_value(date, concentration)

        return timeseries
    
class ConcentrationComputer2:

    def compute(self, 
                inflow_dict, outflow_dict, storage, concentration_dict,
                start_date, end_date):
        """Compute and return the concentration time series.

        Parameters:
        * fractions_list -- dict of fractions timeseries in [0.0, 1.0]
        * concentration_list -- dict of label keys with concentration values in [mg/l]
        
        Computation is based on constant concentration of the fractions
        """
        
        total_outflow = TimeseriesStub()
        for events in enumerate_dict_events(outflow_dict):
            date = events['date']
            del(events['evaporation'])
            del(events['date'])
            total= 0.0
            for key, event in events.items():
                if key in ['outtakes', 'defined_output']:
                    for key_outtake, event_outtake in event.items():
                        total += event_outtake[1]
                else:
                     total += event[1]
            total_outflow.add_value(date, total)
            
            
        start_storage = next(storage.events(start_date, end_date))[1]
        storage_chloride = start_storage * concentration_dict['initial']
        
        delta = TimeseriesStub()
       
        timeseries = TimeseriesStub()
        for events in enumerate_dict_events(dict(tuple(inflow_dict.items()) + (('total_outflow', total_outflow), ('storage', storage)))):
            date = events['date']
            total_outflow = -events['total_outflow'][1]
            storage = events['storage'][1]
            del(events['date'])
            del(events['total_outflow'])
            del(events['storage'])
            
            out = (storage_chloride/storage) * total_outflow
            
            plus = 0.0
            for key, value in events.items():
                if key in ['intakes', 'defined_input']:
                    for key_intake, value_intake in value.items():
                        if key_intake == 'intake_wl_control':
                            plus += value_intake[1] * concentration_dict[key_intake] 
                        else:
                            plus += value_intake[1] * concentration_dict[key_intake.label.program_name] 
                else:
                    plus += value[1] * concentration_dict[key]
            storage_chloride = storage_chloride + plus - out
            timeseries.add_value(date, storage_chloride/storage)
            delta.add_value(date, plus - out)

        return timeseries, delta  
    
