#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The lizard_wbcomputation package implements the computational core of the
# lizard waterbalance Django app.
#
# Copyright (C) 2012 Nelen & Schuurmans
#
# This package is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this package.  If not, see <http://www.gnu.org/licenses/>.

from datetime import timedelta
import logging

from timeseries.timeseriesstub import TimeseriesStub

logger = logging.getLogger(__name__)

class ImpactFromBuckets(object):

    def __init__(self, area):
        self.area = area

    def compute(self, start_date, end_date, substance_string='phosphate'):

        def create_timeseries(area, label):
            timeseries = TimeseriesStub()
            timeseries.location_id = area.location_id
            timeseries.parameter_id = label
            timeseries.units = 'mg/m2/dag'
            timeseries.type = 'instantaneous'
            timeseries.miss_val = '-999.0'
            timeseries.station_name = 'Huh?'
            return timeseries

        logger.debug("WaterbalanceComputer2::get_impact_timeseries_from_buckets")

        logger.debug("Calculating impact from buckets(%s - %s)..." % (
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')))

        min_impact_timeseries = []
        min_impact_timeseries.append(create_timeseries(self.area, 'min_impact_%s_hardened' % substance_string))
        min_impact_timeseries.append(create_timeseries(self.area, 'min_impact_%s_drained' % substance_string))
        min_impact_timeseries.append(create_timeseries(self.area, 'min_impact_%s_flow_off' % substance_string))
        min_impact_timeseries.append(create_timeseries(self.area, 'min_impact_%s_drainage' % substance_string))
        min_impact_timeseries.append(create_timeseries(self.area, 'min_impact_%s_sewer' % substance_string))
        for timeseries in min_impact_timeseries:
            date = start_date
            while date < end_date:
                timeseries.add_value(date + timedelta(hours=23), 0.0)
                date = date + timedelta(1)
        incr_impact_timeseries = []
        incr_impact_timeseries.append(create_timeseries(self.area, 'incr_impact_%s_hardened' % substance_string))
        incr_impact_timeseries.append(create_timeseries(self.area, 'incr_impact_%s_drained' % substance_string))
        incr_impact_timeseries.append(create_timeseries(self.area, 'incr_impact_%s_flow_off' % substance_string))
        incr_impact_timeseries.append(create_timeseries(self.area, 'incr_impact_%s_drainage' % substance_string))
        incr_impact_timeseries.append(create_timeseries(self.area, 'incr_impact_%s_sewer' % substance_string))
        for timeseries in incr_impact_timeseries:
            date = start_date
            while date < end_date:
                timeseries.add_value(date + timedelta(hours=23), 0.0)
                date = date + timedelta(1)
        return min_impact_timeseries, incr_impact_timeseries

