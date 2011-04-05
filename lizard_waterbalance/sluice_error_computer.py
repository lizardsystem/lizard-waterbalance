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

from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import enumerate_dict_events
from timeseries.timeseriesstub import TimeseriesStub


class SluiceErrorComputer:
    "Implements the functionality to compute the sluice error."""

    def compute(self,
            open_water,            
            calc_intake,
            calc_outtake,
            ref_intakes,
            ref_outtakes,
            start_date_calc, 
            end_date_calc):
        """Compute and return the sluice error.

        The sluice error on a specific day is defined as the sum of the
        computed intake and pump values minus the sum of the measured intake
        and pump values. This function returns the TimeseriesStub that contains
        the sluice error for each day in the given horizon.

        Parameters:
          * open_water *
            OpenWater for which to compute the level control
          * level_control *
            pair of TimeseriesStub(s) where the first TimeseriesStub contains
            the total computed discharges of level control intakes and the
            second the total computed discharges of level control pumps
          * start_date *
            the first date for which to compute the sluice error
          * end_date *
            the first date after the last date for which to compute the sluice
            error

        """
        
        total_meas_outtakes = TimeseriesStub()
        sluice_error_timeseries = TimeseriesStub()
        #sluice_error_intake = TimeseriesStub()
        #sluice_error_outtake = TimeseriesStub()
        
        ts = {
        'calc_intake':calc_intake,
        'calc_outtake':calc_outtake,
        'total_intakes':add_timeseries(*ref_intakes.values()),
        'total_outtakes':add_timeseries(*ref_outtakes.values())}
        
        for events in enumerate_dict_events(ts):
            date = events['date']
            
            if date < start_date_calc:
                continue
            elif date > end_date_calc:
                break
                
            intake = events['calc_intake'][1] - events['total_intakes'][1]
            outtake = events['calc_outtake'][1] + events['total_outtakes'][1]
            total = outtake - intake
            sluice_error_timeseries.add_value(date, total)
            #sluice_error_intake.add_value(date, intake)
            #sluice_error_outtake.add_value(date, outtake)
            total_meas_outtakes.add_value(date, -1*events['total_outtakes'][1])
         
        return sluice_error_timeseries, total_meas_outtakes #, sluice_error_intake, sluice_error_outtake

    def _retrieve_measured_timeseries(self):
        """Return the single time series of measured incoming and
        outgoing volume."""
        return self._retrieve_net_timeseries(only_input=False)

    def _retrieve_computed_timeseries(self, level_control):
        """Return the single time series of computed incoming and
        outgoing volume.

        The computed time series of the intakes and pumps is the single time
        series of total incoming and outgoing volume of the intakes and pumps
        that are not used for level control summed with the level control.

        """
        computed_timeseries = self._retrieve_net_timeseries(only_input=True)
        for timeseries in level_control:
            computed_timeseries = add_timeseries(computed_timeseries, timeseries)
        return computed_timeseries

    def _retrieve_net_timeseries(self, only_input):
        """Return the time series of total incoming and outgoing volume.

        Parameter:
          * only_input *
            holds if and only if only this method should only consider intakes
            and pumps that are not used for level control

        This method also uses the instance variables self.open_water,
        self.start_date and self.end_date. Although these parameters
        could also be passed as arguments, we decided to 'pass them'
        als instance variables to allow for a shorter method
        signature.

        """

        net_timeseries = TimeseriesStub()
        timeseries = self.open_water.retrieve_incoming_timeseries(only_input=only_input).values()
        timeseries += self.open_water.retrieve_outgoing_timeseries(only_input=only_input).values()
        for events in enumerate_events(*timeseries):
            date = events[0][0]
            if date < self.start_date:
                continue
            if date >= self.end_date:
                break
            net_timeseries.add_value(date, sum(e[1] for e in events))
        return net_timeseries
