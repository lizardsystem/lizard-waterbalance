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
from timeseries.timeseriesstub import TimeseriesStub


class LoadComputer:

    def compute(self, area, concentration_string,
                flow_dict, concentration_dict,
                start_date, end_date, nutricalc_timeseries=None):
        """Compute and return the concentration time series.

        Parameters:
          *area*
            area for which to compute the load
          *concentration_string*
            either 'min' or 'incr'
          *flow_list*
            dictionary of incoming waterflows
          *concentration_list*
            dict of label keys with concentration values in [mg/l]

        This method returns a dictionary of flow to time series. The flow can
        be (specified by) a string such as 'precipitation', 'seepage' or
        'drained', or can be (specified by) a PumpingStation.

        In an earlier version of this method the keys of the returned
        dictionary where always a string but that has been changed to solve the
        problem reported in ticket:2542.

        Remarks:
          * flows_dict['defined_input'] is a dictionary from intake to time
            series
          * this method would benefit from additional documentation and a
            review

        """

        loads = {}

        if nutricalc_timeseries:
            flow_dict['nutricalc'] = nutricalc_timeseries

        for events in enumerate_dict_events(flow_dict):
            date = events['date']
            if date < start_date:
                continue
            if date >= end_date:
                break

            del(events['date'])

            if nutricalc_timeseries:
                del(events['drained'])
                del(events['undrained'])

            for key, value in events.items():
                # key never seems to be equal to 'intakes'
                if key in ['intakes', 'defined_input']:
                    for key_intake, value_intake in value.items():
                        if key_intake == 'intake_wl_control':
                            # if key is indeed never equal to 'intakes',
                            # key_intake will never be equal to
                            # 'intake_wl_control'
                            load = value_intake[1] * \
                                   concentration_dict[key_intake]
                            label = 'intake_wl_control'
                        else:
                            load = value_intake[1] * \
                                   concentration_dict[key_intake.label.program_name]
                            label = key_intake
                        loads.setdefault(label, TimeseriesStub()).add_value(date, load)
                    continue
                elif key == 'nutricalc':
                    label = key
                    load = value[1]
                else:
                    label = key
                    if key in ['precipitation', 'seepage']:
                        attr_string = '%s_concentr_phosphate_%s' % \
                            (concentration_string, key)
                        load = value[1] * getattr(area, attr_string)
                    else:
                        load = value[1] * concentration_dict[key]

                # label = key
                # if key in ['precipitation', 'seepage']:
                #     attr_string = '%s_concentr_phosphate_%s' % \
                #         (concentration_string, key)
                #     load = value[1] * getattr(area, attr_string)
                # else:
                #     continue

                loads.setdefault(label, TimeseriesStub()).add_value(date, load)

        return loads
