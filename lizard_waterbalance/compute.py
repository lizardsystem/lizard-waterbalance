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
# Initial date:       2010-11-26
#
#******************************************************************************

from timeseriesstub import TimeseriesStub


def compute_seepage(bucket, date, seepage):
    """Return the seepage of the given bucket on the given date.

    Parameters:
    * bucket -- bucket for which to compute the seepage
    * date -- date for which to compute the seepage
    * seepage -- time series that specifies the seepage

    """
    # with regard to the factor 0.001 in the next line, seepage is specified
    # in [mm/day] but surface in [m]: 1 [mm] == 0.001 [m]
    return (bucket.surface * seepage.get_value(date)) / 1000.0


def compute_net_precipitation(bucket,
                              previous_storage,
                              current_precipitation,
                              current_evaporation):
    """Return the net precipitation of today.

    With net precipitation, we mean the volume difference caused by
    precipitation and evaporation.

    Parameters:
    * bucket -- bucket for which to compute the net precipitatio
    * previous_storage -- water storage in the bucket on the previous day
    * current_precipitation -- precipitation of today
    * current_evaporation -- evaporation of today

    """
    equi_storage = bucket.equi_water_level * bucket.surface
    if previous_storage > equi_storage:
        evaporation_factor = bucket.crop_evaporation_factor
    else:
        evaporation_factor = bucket.min_crop_evaporation_factor

    net_precipitation = current_precipitation
    net_precipitation = net_precipitation -\
                        current_evaporation * evaporation_factor
    # with regard to the factor 0.001 in the next line, precipitation and
    # evaporation are specified in [mm/day] but surface in [m]: 1 [mm] == 0.001
    # [m]
    return net_precipitation * bucket.surface / 1000.0


def compute_net_drainage(bucket, previous_storage):
    """Return the net drainage of today.

    With net drainage, we mean the volumwe difference caused by drainage and
    infiltration.

    Parameters:
    * bucket -- bucket for which to compute the net drainage
    * previous_storage -- water storage in the bucket on the previous day

    """
    equi_storage = bucket.equi_water_level * bucket.surface
    if previous_storage > equi_storage:
        net_drainage = -previous_storage * bucket.drainage_fraction
    elif previous_storage < equi_storage:
        net_drainage = -previous_storage * bucket.infiltration_fraction
    else:
        net_drainage = 0
    return net_drainage

def compute(bucket, start_date, end_date, precipitation, evaporation, seepage):
    """Compute and return the waterbalance time series of the given bucket.

    This method computes the water level, flow off and net drainage time series
    of the given bucket and returns them as a triple.

    Parameters:
    * bucket -- bucket for which to compute the waterbalance (time series)
    * start_date -- first date for which to compute the waterbalance
    * end_date -- last date for which to compute the waterbalance
    * precipitation -- time serie that specifies the precipitation
    * evaporation -- time serie that specifies the evaporation
    * seepage -- time serie that specifies the seepage

    Please note that this method uses the initial water level of the bucket as
    the water level at the end of the day that precedes the start date.

    """

    V_max = bucket.max_water_level * bucket.porosity * bucket.surface
    V_previous_day = bucket.init_water_level * bucket.surface

    current_precipitation = precipitation.get_value(start_date)
    current_evaporation = evaporation.get_value(start_date)
    Q_precipitation = compute_net_precipitation(bucket,
                                                V_previous_day,
                                                current_precipitation,
                                                current_evaporation)

    Q_seepage = compute_seepage(bucket, start_date, seepage)

    Q_drain = compute_net_drainage(bucket, V_previous_day)

    Q_in = Q_drain + Q_precipitation + Q_seepage

    if V_previous_day + Q_in < V_max:
        V_today = V_previous_day + Q_in
        Q_afst = 0
    else:
        V_today = V_max
        Q_afst = -(V_previous_day + Q_in - V_max)

    water_level = TimeseriesStub(0)
    water_level.add_value(start_date, V_today / bucket.surface)

    flow_off = TimeseriesStub(0)
    flow_off.add_value(start_date, Q_afst)

    net_drainage = TimeseriesStub(0)
    net_drainage.add_value(start_date, Q_drain)

    return (water_level, flow_off, net_drainage)
