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
# initial programmer: Bastiaan Roos
# initial version:    2012-09-28
#
#******************************************************************************

import uuid
import logging
import datetime

logger = logging.getLogger(__name__)




def validate_settings(area):
    """

    :param area: Area class object with all settings
    :return: tuple with number of errors and warnings
    """

    errors = 0
    warnings = 0

    if area.bottom_height > area.init_water_level:
        logger.error('bodemhoogte ligt boven initiele waterhoogte')
        errors += 1


    for ts_name in ['minimum_level',
                    'maximum_level']:
        value_error = False

        for event in getattr(area,ts_name).events():
            if event[1] < area.bottom_height:
                value_error = True

        if value_error:
            logger.error('Het ingestelde %s moet hoger of gelijk liggen aan het streefpeil'%ts_name)
            errors += 1

    for prop in ['concentr_chloride_precipitation',
                'concentr_chloride_seepage',
                'corresponding_parameter_id',
                'incr_concentr_nitrogen_precipitation',
                'incr_concentr_nitrogen_seepage',
                'incr_concentr_phosphate_precipitation',
                'incr_concentr_phosphate_seepage',
                'incr_concentr_sulphate_precipitation',
                'incr_concentr_sulphate_seepage',
                'ini_con_cl',
                'init_concentration',
                'max_intake', 'max_outtake',
                'min_concentr_nitrogen_precipitation',
                'min_concentr_nitrogen_seepage',
                'min_concentr_phosphate_precipitation',
                'min_concentr_phosphate_seepage',
                'min_concentr_sulphate_precipitation',
                'min_concentr_sulphate_seepage',
                'max_intake',
                'max_outtake',
                'surface']:
        if getattr(area, prop) < 0:
            logger.error('instelling %s van het gebied moet groter of gelijk zijn aan 0'%prop)
            errors += 1


    for bucket in area.buckets:
        for prop in ['bottom_equi_water_level',
                    'equi_water_level',
                    ]:
            setattr(bucket,prop, 0)

        #warning: tussen min en max peil
        if bucket.bottom_init_water_level > bucket.bottom_max_water_level:
            logger.warning("Het initiele peil in bucket '%s' (onderste bakje) ligt boven het maximum peil."%bucket.name)
            warnings += 1
        if bucket.bottom_init_water_level < bucket.bottom_min_water_level:
            logger.warning("Het initiele peil in bucket '%s' (onderste bakje) ligt onder het minimum peil."%bucket.name)
            warnings += 1
        if bucket.init_water_level > bucket.max_water_level:
            logger.warning("Het initiele peil in bucket '%s' ligt boven het maximum peil."%bucket.name)
            warnings += 1
        if bucket.init_water_level < bucket.min_water_level:
            logger.warning("Het initiele peil in bucket '%s' ligt onder het minimum peil."%bucket.name)
            warnings += 1

        #groter of gelijk aan 0
        for prop in [
            'bottom_max_water_level',
            'max_water_level',
            'concentr_chloride_drainage_indraft',
            'concentr_chloride_flow_off',
            'incr_concentr_nitrogen_drainage_indraft',
            'incr_concentr_nitrogen_flow_off',
            'incr_concentr_phosphate_drainage_indraft',
            'incr_concentr_phosphate_flow_off',
            'incr_concentr_sulphate_drainage_indraft',
            'incr_concentr_sulphate_flow_off',
            'min_concentr_nitrogen_drainage_indraft',
            'min_concentr_nitrogen_flow_off',
            'min_concentr_phosphate_drainage_indraft',
            'min_concentr_phosphate_flow_off',
            'min_concentr_sulphate_drainage_indraft',
            'min_concentr_sulphate_flow_off',
            'surface',]:

            if getattr(bucket, prop) < 0:
                logger.error("waarde %s van bucket '%s' moet groter of gelijk zijn aan 0"%(prop, bucket.name))
                errors += 1

        #kleiner of gelijk aan 0
        for prop in ['bottom_min_water_level',
                    'min_water_level',]:

            if getattr(bucket, prop) > 0:
                logger.error("waarde %s van bucket '%s' moet kleiner of gelijk zijn aan 0"%(prop, bucket.name))
                errors += 1


        #kleiner of gelijk aan 0
        for prop in ['bottom_crop_evaporation_factor',
                     'bottom_drainage_fraction',
                     'bottom_indraft_fraction',
                     'bottom_min_crop_evaporation_factor',
                     'bottom_porosity',
                     'crop_evaporation_factor',
                     'drainage_fraction',
                     'indraft_fraction',
                     'min_crop_evaporation_factor',
                     'porosity',]:

            if getattr(bucket, prop) < 0 or getattr(bucket, prop) > 1:
                logger.error("waarde %s van bucket '%s' moet tussen 0 en 1 liggen"%(prop, bucket.name))
                errors += 1







    #make flow_off and drainage timeseries equidistant and inside timerange
    #same for evaporation and drainage

    #    if not fill_below_minimum_with_indraft and bucket.min_water_level == None:
    #        logger.warming("Warning, minimum level is not set for %s, default value 0 taken for calculation (level below minimum level is not allowed for this bucket type)"%bucket.name)
    #        bucket.min_water_level = 0




    return (errors, warnings)