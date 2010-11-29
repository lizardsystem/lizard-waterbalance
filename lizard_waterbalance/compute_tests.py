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

from unittest import TestCase

from lizard_waterbalance.models import Bucket

bucket_column_names = [
    "uitspoel", "code", "indraft", "surface", "ol minimum level", "flow_off",
    "infiltration", "bl min. Gewasverdampingsfactor (-)", "bl init level",
    "bl max level", "ol max level", "ol gewasverdampingsfactor (-)",
    "ol min. Gewasverdampingsfactor (-)", "ol porositeit / bergingsruimte",
    "bl minimum level", "open_water", "ol init level", "ol equilibrium level",
    "bl equilibrium level", "ol f_intrek", "ol_volume",
    "bl porositeit / bergingsruimte", "nr", "bl gewasverdampingsfactor (-)",
    "name", "bl_volume", "computed_flow_off", "ol f_uitpoel", "bl f_uitpoel",
    "seepage", "bl f_intrek"]

bucket_values = [
    "B_3_1", "B_3", "B_3_0", "2950181.83812", "", "B_3_4", "B_3_3", "0.75",
    "0.35", "0.7", "", "", "", "", "0.0", "O_0", "", "", "0.0", "", "", "0.2",
    "6", "1.0", "landelijk", "B_3_5", "", "", "0.02", "B_3_2", "0.02"]

bucket_spec = dict(zip(bucket_column_names, bucket_values))

class computeTestSuite(TestCase):

    def test_a(self):
        bucket = Bucket()
        # we initialize the input fields
        bucket.name = bucket_spec['name']
        bucket.surface = bucket_spec['surface']
        # bucket.seepage = link to input time serie for *kwel*
        bucket.porosity = bucket_spec['bl porositeit / bergingsruimte']
        bucket.crop_evaporation_factor = bucket_spec['bl gewasverdampingsfactor (-)']
        bucket.min_crop_evaporation_factor = bucket_spec['bl min. Gewasverdampingsfactor (-)']
        bucket.drainage_fraction= bucket_spec['bl f_uitspoel']
        bucket.infiltration_fraction = bucket_spec['bl f_intrek']
        bucket.max_water_level = bucket_spec['bl max level']
        bucket.equi_water_level = bucket_spec['bl equilibrium level']
        bucket.min_water_level = bucket_spec['bl minimum level']
        bucket.init_water_level = bucket_spec['bl init level']
        bucket.external_discharge = bucket_spec['bl_f_uitpoel']
