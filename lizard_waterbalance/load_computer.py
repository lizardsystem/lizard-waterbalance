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


class LoadComputer:

    def compute(self, 
                flow_dict, concentration_dict,
                start_date, end_date, nutricalc_timeseries=None):
        """Compute and return the concentration time series.

        Parameters:
        * flow_list -- dict of incoming waterflows
        * concentration_list -- dict of label keys with concentration values in [mg/l]


        """
           
        loads = {}
        
        if nutricalc_timeseries:
            flow_dict['nutricalc'] = nutricalc_timeseries
        
        
        first_ts = True
        for events in enumerate_dict_events(flow_dict):
            date = events['date']
            del(events['date'])
            
            if nutricalc_timeseries:
                del(events['drainage'])
                del(events['undrained'])
            
            for key, value in events.items():
                if key in ['intakes', 'defined_input']:
                    for key_intake, value_intake in value.items():
                        if key_intake == 'intake_wl_control':
                            load = value_intake[1] * concentration_dict[key_intake]
                            label = 'intake_wl_control'
                        else:
                            load = value_intake[1] * concentration_dict[key_intake.label.program_name]
                            label = key_intake.label.program_name
                elif key == 'nutricalc':
                    label = key
                    load = event['nutricalc']
                else:
                    label = key
                    load = value[1] * concentration_dict[key]
            
                if first_ts:
                    loads[label] = TimeseriesStub()
                
                loads[label].add_value(date, load)
            first_ts = False

        return loads
