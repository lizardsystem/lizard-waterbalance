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

from datetime import datetime
from unittest import TestCase

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.compute import compute
from lizard_waterbalance.compute import compute_net_drainage
from lizard_waterbalance.compute import compute_net_precipitation
from lizard_waterbalance.compute import compute_seepage
from lizard_waterbalance.timeseriesstub import TimeseriesStub


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

bucket = Bucket()
# we initialize the input fields
bucket.name = bucket_spec['name']
bucket.surface = int(float(bucket_spec['surface']))
# bucket.seepage = link to input time serie for *kwel*
bucket.porosity = float(bucket_spec['bl porositeit / bergingsruimte'])
bucket.crop_evaporation_factor = float(bucket_spec['bl gewasverdampingsfactor (-)'])
bucket.min_crop_evaporation_factor = float(bucket_spec['bl min. Gewasverdampingsfactor (-)'])
bucket.drainage_fraction= float(bucket_spec['bl f_uitpoel'])
bucket.infiltration_fraction = float(bucket_spec['bl f_intrek'])
bucket.max_water_level = float(bucket_spec['bl max level'])
bucket.equi_water_level = float(bucket_spec['bl equilibrium level'])
bucket.min_water_level = float(bucket_spec['bl minimum level'])
bucket.init_water_level = float(bucket_spec['bl init level'])
bucket.external_discharge = 0 # not known in bucket_spec

evaporation = TimeseriesStub(0)
precipitation = TimeseriesStub(0)
seepage = TimeseriesStub(0)

today = datetime(2010, 11, 29)
(water_level, flow_off, net_drainage) = \
              compute(bucket, today, today, evaporation, precipitation, seepage)

print bucket

class computeTestSuite(TestCase):

    def setUp(self):
        self.bucket = Bucket()
        # we initialize the input fields
        self.bucket.name = bucket_spec['name']
        self.bucket.surface = int(float(bucket_spec['surface']))
        # self.bucket.seepage = link to input time serie for *kwel*
        self.bucket.porosity = float(bucket_spec['bl porositeit / bergingsruimte'])
        self.bucket.crop_evaporation_factor = float(bucket_spec['bl gewasverdampingsfactor (-)'])
        self.bucket.min_crop_evaporation_factor = float(bucket_spec['bl min. Gewasverdampingsfactor (-)'])
        self.bucket.drainage_fraction= float(bucket_spec['bl f_uitpoel'])
        self.bucket.infiltration_fraction = float(bucket_spec['bl f_intrek'])
        self.bucket.max_water_level = float(bucket_spec['bl max level'])
        self.bucket.equi_water_level = float(bucket_spec['bl equilibrium level'])
        self.bucket.min_water_level = float(bucket_spec['bl minimum level'])
        self.bucket.init_water_level = float(bucket_spec['bl init level'])
        self.bucket.external_discharge = 0 # not known in bucket_spec

    def test_a(self):
        """Test compute_seepage on zero seepage.

        """
        seepage = TimeseriesStub(0)
        today = datetime(2010, 11, 30)
        self.assertAlmostEqual(0.0, compute_seepage(self.bucket, today, seepage))

    def test_b(self):
        """Test compute_seepage on non-zero seepage.

        """
        seepage = TimeseriesStub(10) # specifies a seepage of 10 mm / day
        today = datetime(2010, 11, 30)
        expected_seepage = 29501.81
        computed_seepage = compute_seepage(self.bucket, today, seepage)
        self.assertAlmostEqual(expected_seepage, computed_seepage)

    def test_c(self):
        """Test compute_net_precipitation on zero precipitation and evaporation.

        """
        self.bucket.equi_water_level = 0.50
        previous_storage = bucket.init_water_level * bucket.surface
        current_precipitation = 0
        current_evaporation = 0
        expected_value = 0.0
        computed_value = compute_net_precipitation(self.bucket,
                                                   previous_storage,
                                                   current_precipitation,
                                                   current_evaporation)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_d(self):
        """Test compute_net_precipitation on more precipitation than evaporation.

        """
        self.bucket.equi_water_level = 0.50
        previous_storage = 1400000.00
        current_precipitation = 20
        current_evaporation = 5
        expected_value = 47940.44
        computed_value = compute_net_precipitation(self.bucket,
                                                   previous_storage,
                                                   current_precipitation,
                                                   current_evaporation)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_e(self):
        """Test compute_net_precipitation on more evaporation than precipitation.

        """
        self.bucket.equi_water_level = 0.50
        previous_storage = 1400000.00
        current_precipitation = 5
        current_evaporation = 20
        expected_value = -29501.81
        computed_value = compute_net_precipitation(self.bucket,
                                                   previous_storage,
                                                   current_precipitation,
                                                   current_evaporation)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_f(self):
        """Test compute_net_drainage on less previous day storage than equi storage.

        """
        self.bucket.infiltration_fraction = 0.04
        previous_storage = 1400000.00
        expected_value = -28000
        computed_value = compute_net_drainage(self.bucket, previous_storage)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_g(self):
        """Test compute returns the right water level.

        """
        evaporation = TimeseriesStub(20)
        precipitation = TimeseriesStub(5)
        seepage = TimeseriesStub(10)
        self.bucket.infiltration_fraction = 0.04
        previous_storage = 1400000.00

        today = datetime(2010, 11, 29)
        (water_level, flow_off, net_drainage) = \
                      compute(bucket, today, today, evaporation, precipitation, seepage)

    def test_z(self):

        evaporation = TimeseriesStub(0)
        precipitation = TimeseriesStub(0)
        seepage = TimeseriesStub(0)

        today = datetime(2010, 11, 29)
        (water_level, flow_off, net_drainage) = \
                      compute(bucket, today, today, evaporation, precipitation, seepage)



