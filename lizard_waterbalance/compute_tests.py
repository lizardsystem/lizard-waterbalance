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
from lizard_waterbalance.compute import compute
from lizard_waterbalance.compute import compute_net_drainage
from lizard_waterbalance.compute import compute_net_precipitation
from lizard_waterbalance.compute import compute_seepage
from lizard_waterbalance.compute import compute_timeseries
from lizard_waterbalance.mock import Mock
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
        seepage = 0
        self.assertAlmostEqual(0.0, compute_seepage(self.bucket, seepage))

    def test_b(self):
        """Test compute_seepage on non-zero seepage.

        """
        seepage = 10
        expected_seepage = 29501.81
        computed_seepage = compute_seepage(self.bucket, seepage)
        self.assertAlmostEqual(expected_seepage, computed_seepage)

    def test_c(self):
        """Test compute_net_precipitation on zero precipitation and evaporation.

        """
        self.bucket.equi_water_level = 0.50
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        precipitation = 0
        evaporation = 0
        expected_value = 0.0
        computed_value = compute_net_precipitation(self.bucket,
                                                   previous_volume,
                                                   precipitation,
                                                   evaporation)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_d(self):
        """Test compute_net_precipitation on more precipitation than evaporation.

        """
        self.bucket.equi_water_level = 0.50
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        precipitation = 20
        evaporation = 5
        expected_value = 47940.44
        computed_value = compute_net_precipitation(self.bucket,
                                                   previous_volume,
                                                   precipitation,
                                                   evaporation)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_e(self):
        """Test compute_net_precipitation on more evaporation than precipitation.

        """
        self.bucket.equi_water_level = 0.50
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        precipitation = 5
        evaporation = 20
        expected_value = -29501.81
        computed_value = compute_net_precipitation(self.bucket,
                                                   previous_volume,
                                                   precipitation,
                                                   evaporation)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_f(self):
        """Test compute_net_drainage on less previous day storage than equi storage.

        """
        self.bucket.equi_water_level = 0.50
        self.bucket.infiltration_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        expected_value = -41302.53
        computed_value = compute_net_drainage(self.bucket, previous_volume)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_g(self):
        """Test compute_net_drainage on more previous day storage than equi storage.

        """
        self.bucket.init_water_level = 0.65
        self.bucket.infiltration_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        expected_value = -38352.35
        computed_value = compute_net_drainage(self.bucket, previous_volume)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_h(self):
        """Test compute returns the correct water level.

        """
        self.bucket.infiltration_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        evaporation = 20
        precipitation = 5
        seepage = 10

        expected_water_level = 0.14
        (water_level, flow_off, net_drainage) = compute(self.bucket,
                                                        previous_volume,
                                                        evaporation,
                                                        precipitation,
                                                        seepage)
        self.assertAlmostEqual(expected_water_level, water_level)

    def test_i(self):
        """Test compute returns the correct flow off.

        """
        self.bucket.equi_water_level = 0.50
        self.bucket.infiltration_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        evaporation = 20
        precipitation = 5
        seepage = 10

        expected_flow_off = -655677.73
        (water_level, flow_off, net_drainage) = compute(self.bucket,
                                                        previous_volume,
                                                        evaporation,
                                                        precipitation,
                                                        seepage)
        self.assertAlmostEqual(expected_flow_off, flow_off, 2)

    def test_j(self):
        """Test compute returns the correct net drainage.

        """
        self.bucket.equi_water_level = 0.50
        self.bucket.infiltration_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        evaporation =  20
        precipitation = 5
        seepage = 10

        expected_drainage = -41302.53
        (water_level, flow_off, net_drainage) = compute(self.bucket,
                                                        previous_volume,
                                                        evaporation,
                                                        precipitation,
                                                        seepage)
        self.assertAlmostEqual(expected_drainage, net_drainage, 2)

    def test_k(self):
        """Test compute_timeseries starts with the correct initial water volume."""
        evaporation = TimeseriesStub(20)
        precipitation = TimeseriesStub(5)
        seepage = TimeseriesStub(10)
        mock = Mock()
        # we do not need the return value of the next call and we discard it
        compute_timeseries(self.bucket,
                           evaporation,
                           precipitation,
                           seepage,
                           mock.compute)
        calls_to_compute = mock.getNamedCalls('compute')
        self.assertTrue(len(calls_to_compute) > 0)
        supplied_volume = calls_to_compute[0].getParam(1)
        expected_volume = self.bucket.init_water_level * self.bucket.surface
        self.assertAlmostEqual(supplied_volume, expected_volume)
