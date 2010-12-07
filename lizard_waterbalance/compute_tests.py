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
from datetime import timedelta
from unittest import TestCase

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.compute import BucketOutcome
from lizard_waterbalance.compute import compute
from lizard_waterbalance.compute import compute_net_drainage
from lizard_waterbalance.compute import compute_net_precipitation
from lizard_waterbalance.compute import compute_seepage
from lizard_waterbalance.compute import compute_timeseries
from lizard_waterbalance.compute import enumerate_events
from lizard_waterbalance.compute import open_water_compute
from lizard_waterbalance.mock import Mock
from lizard_waterbalance.timeseriesretriever import TimeseriesRetriever
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

        expected_storage = 413025.34
        (storage, flow_off, net_drainage) = compute(self.bucket,
                                                    previous_volume,
                                                    evaporation,
                                                    precipitation,
                                                    seepage)
        self.assertAlmostEqual(expected_storage, storage)

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
        (storage, flow_off, net_drainage) = compute(self.bucket,
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
        (storage, flow_off, net_drainage) = compute(self.bucket,
                                                    previous_volume,
                                                    evaporation,
                                                    precipitation,
                                                    seepage)
        self.assertAlmostEqual(expected_drainage, net_drainage, 2)

    def test_k(self):
        """Test compute_timeseries starts with the correct initial water volume."""
        today = datetime(2010,12,2)
        evaporation = TimeseriesStub(0)
        evaporation.add_value(today, 20)
        precipitation = TimeseriesStub(0)
        precipitation.add_value(today, 5)
        seepage = TimeseriesStub(0)
        seepage.add_value(today, 10)
        mock = Mock({"compute": (0, 0, 0)})
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

    def test_l(self):
        """Test compute_timeseries starts with the correct time serie values."""
        today = datetime(2010,12,2)
        tomorrow = datetime(2010,12,3)
        evaporation = TimeseriesStub(0)
        evaporation.add_value(today, 20)
        evaporation.add_value(tomorrow, 30)
        precipitation = TimeseriesStub(0)
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        seepage = TimeseriesStub(0)
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        mock = Mock({"compute": (0, 0, 0)})
        # we do not need the return value of the next call and we discard it
        compute_timeseries(self.bucket,
                           evaporation,
                           precipitation,
                           seepage,
                           mock.compute)
        calls_to_compute = mock.getNamedCalls('compute')
        self.assertTrue(len(calls_to_compute) > 0)
        supplied_precipitation = calls_to_compute[0].getParam(2)
        expected_precipitation = 20
        self.assertAlmostEqual(supplied_precipitation, expected_precipitation)
        supplied_evaporation = calls_to_compute[0].getParam(3)
        expected_evaporation = 5
        self.assertAlmostEqual(supplied_evaporation, expected_evaporation)
        supplied_seepage = calls_to_compute[0].getParam(4)
        expected_seepage = 10
        self.assertAlmostEqual(supplied_seepage, expected_seepage)

    def test_m(self):
        """Test compute_timeseries supplies the correct time serie values."""
        today = datetime(2010,12,2)
        tomorrow = datetime(2010,12,3)
        evaporation = TimeseriesStub(0)
        evaporation.add_value(today, 20)
        evaporation.add_value(tomorrow, 30)
        precipitation = TimeseriesStub(0)
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        seepage = TimeseriesStub(0)
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        mock = Mock({"compute": (0, 0, 0)})
        # we do not need the return value of the next call and we discard it
        compute_timeseries(self.bucket,
                           evaporation,
                           precipitation,
                           seepage,
                           mock.compute)
        calls_to_compute = mock.getNamedCalls('compute')
        self.assertEqual(2, len(calls_to_compute))
        supplied_precipitation = calls_to_compute[1].getParam(2)
        expected_precipitation = 30
        self.assertAlmostEqual(supplied_precipitation, expected_precipitation)
        supplied_evaporation = calls_to_compute[1].getParam(3)
        expected_evaporation = 10
        self.assertAlmostEqual(supplied_evaporation, expected_evaporation)
        supplied_seepage = calls_to_compute[1].getParam(4)
        expected_seepage = 20
        self.assertAlmostEqual(supplied_seepage, expected_seepage)

class enumerate_eventsTestSuite(TestCase):

    def test_a(self):
        today = datetime(2010,12,2)
        tomorrow = datetime(2010,12,3)
        precipitation = TimeseriesStub(0)
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        evaporation = TimeseriesStub(0)
        evaporation.add_value(today, 20)
        evaporation.add_value(tomorrow, 30)
        seepage = TimeseriesStub(0)
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        events = [event for event in enumerate_events(precipitation, evaporation, seepage)]

        expected_events = [((today, 5), (today, 20), (today, 10)),
                           ((tomorrow, 10), (tomorrow, 30), (tomorrow, 20))]
        self.assertEqual(expected_events, events)

    def test_b(self):
        today = datetime(2010,12,2)
        tomorrow = datetime(2010,12,3)
        precipitation = TimeseriesStub(0)
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        evaporation = TimeseriesStub(0)
        evaporation.add_value(tomorrow, 30)
        seepage = TimeseriesStub(0)
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        events = [event for event in enumerate_events(precipitation, evaporation, seepage)]

        expected_events = [((tomorrow, 10), (tomorrow, 30), (tomorrow, 20))]
        self.assertEqual(expected_events[0], events[0])


class OpenWaterComputeTestSuite(TestCase):

    def setUp(self):
        self.open_water = OpenWater()
        self.open_water.name = "Aetseveldsepolder oost - openwater"
        self.open_water.surface = int(float("402613.682123"))
        self.bucket = Bucket()
        self.bucket.name = "Aetseveldsepolder oost - landelijk"
        self.bucket.surface_type = Bucket.UNDRAINED_SURFACE
        self.buckets = [self.bucket]
        self.bucket_computers = dict([(Bucket.UNDRAINED_SURFACE, None)])
        self.pumping_stations = []
        self.today = datetime(2010, 12, 6)
        self.next_week = self.today + timedelta(7)
    def test_a(self):
        """Test open_water_compute creates time series for the open water and the bucket."""
        mock_compute = Mock({"compute": BucketOutcome()}).compute
        self.bucket_computers[Bucket.UNDRAINED_SURFACE] = mock_compute
        timeseries_retriever = Mock()
        timeseries = open_water_compute(self.open_water, self.buckets,
                                        self.bucket_computers,
                                        self.pumping_stations,
                                        timeseries_retriever)
        self.assertEqual(2, len(timeseries.keys()))
        self.assertTrue(self.bucket.name in timeseries.keys())
        self.assertTrue(self.open_water.name in timeseries.keys())

    def test_b(self):
        """Test open_water_compute stores the time series for the bucket."""
        outcome = BucketOutcome()
        outcome.storage.add_value(self.today, 0.6)
        outcome.storage.add_value(self.next_week, 0.8)
        outcome.flow_off.add_value(self.today, 0.1)
        outcome.flow_off.add_value(self.next_week, 0.2)
        outcome.net_drainage.add_value(self.today, 0.2)
        outcome.net_drainage.add_value(self.next_week, 0.2)
        mock_compute = Mock({"compute": outcome}).compute
        self.bucket_computers[Bucket.UNDRAINED_SURFACE] = mock_compute
        timeseries_retriever = Mock()
        timeseries = open_water_compute(self.open_water, self.buckets,
                                        self.bucket_computers,
                                        self.pumping_stations,
                                        timeseries_retriever)
        timeseries_bucket = timeseries[self.bucket.name]
        self.assertEqual(outcome.storage, timeseries_bucket.storage)
        self.assertEqual(outcome.flow_off, timeseries_bucket.flow_off)
        self.assertEqual(outcome.net_drainage, timeseries_bucket.net_drainage)

    def test_c(self):
        """Test open_water_compute stores the precipitation for the open water."""
        buckets = []
        bucket_computers = []
        timeseries = TimeseriesStub(0)
        timeseries.add_value(self.today, 10)
        timeseries_retriever = Mock({"get_timeseries": timeseries})
        timeseries = open_water_compute(self.open_water, buckets,
                                        bucket_computers,
                                        self.pumping_stations,
                                        timeseries_retriever)
        timeseries_open_water = timeseries[self.open_water.name]
        self.assertTrue('precipitation' in timeseries_open_water.keys())


