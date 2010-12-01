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


def compute_seepage(bucket, seepage):
    """Return the seepage of the given bucket on the given date.

    Parameters:
    * bucket -- bucket for which to compute the seepage
    * date -- date for which to compute the seepage
    * seepage -- seepage in [mm/day]

    """
    # with regard to the factor 0.001 in the next line, seepage is specified
    # in [mm/day] but surface in [m]: 1 [mm] == 0.001 [m]
    return (bucket.surface * seepage) / 1000.0


def compute_net_precipitation(bucket,
                              previous_volume,
                              precipitation,
                              evaporation):
    """Return the net precipitation of today.

    With net precipitation, we mean the volume difference caused by
    precipitation and evaporation.

    Parameters:
    * bucket -- bucket for which to compute the net precipitation
    * previous_volume -- water volume of the bucket the day before
    * precipitation -- precipitation of today in [mm/day]
    * evaporation -- evaporation of today in [mm/day]

    """
    equi_volume = bucket.equi_water_level * bucket.surface
    if previous_volume > equi_volume:
        evaporation_factor = bucket.crop_evaporation_factor
    else:
        evaporation_factor = bucket.min_crop_evaporation_factor

    net_precipitation = precipitation - evaporation * evaporation_factor
    # with regard to the factor 0.001 in the next line, precipitation and
    # evaporation are specified in [mm/day] but surface in [m]: 1 [mm] == 0.001
    # [m]
    return net_precipitation * bucket.surface / 1000.0


def compute_net_drainage(bucket, previous_volume):
    """Return the net drainage of today.

    With net drainage, we mean the volume difference caused by drainage and
    infiltration.

    Parameters:
    * bucket -- bucket for which to compute the net drainage
    * previous_volume -- water volume of the bucket the day before

    """
    equi_volume = bucket.equi_water_level * bucket.surface
    if previous_volume > equi_volume:
        net_drainage = -previous_volume * bucket.drainage_fraction
    elif previous_volume < equi_volume:
        net_drainage = -previous_volume * bucket.infiltration_fraction
    else:
        net_drainage = 0
    return net_drainage

def compute(bucket, previous_volume, precipitation, evaporation, seepage):
    """Compute and return the waterbalance of the given bucket.

    This method computes the water level, flow off and net drainage of the
    given bucket and returns them as a triple.

    Parameters:
    * bucket -- bucket for which to compute the waterbalance
    * previous_volume -- water volume of the bucket the day before
    * precipitation -- precipitation for the bucket in [mm/day]
    * evaporation -- evaporation for the bucket in [mm/day]
    * seepage -- seepage for the bucket in [mm/day]

    """
    max_volume = bucket.max_water_level * bucket.porosity * bucket.surface

    Q_precipitation = compute_net_precipitation(bucket,
                                                previous_volume,
                                                precipitation,
                                                evaporation)
    Q_seepage = compute_seepage(bucket, seepage)
    Q_drain = compute_net_drainage(bucket, previous_volume)
    Q_in = Q_drain + Q_precipitation + Q_seepage

    if previous_volume + Q_in < max_volume:
        volume = previous_volume + Q_in
        Q_afst = 0
    else:
        volume = max_volume
        Q_afst = -(previous_volume + Q_in - max_volume)

    return (volume / bucket.surface, Q_afst, Q_drain)
