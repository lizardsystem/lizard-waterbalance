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
from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_waterbalance.compute import BucketOutcome
from lizard_waterbalance.compute import BucketSummarizer
from lizard_waterbalance.compute import BucketsSummary
from lizard_waterbalance.compute import compute
from lizard_waterbalance.compute import compute_net_drainage
from lizard_waterbalance.compute import compute_net_precipitation
from lizard_waterbalance.compute import compute_seepage
from lizard_waterbalance.compute import compute_timeseries
from lizard_waterbalance.compute import retrieve_net_intake
from lizard_waterbalance.compute import total_daily_bucket_outcome
from lizard_waterbalance.compute import WaterbalanceComputer
from lizard_waterbalance.mock import Mock
from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.store import store_waterbalance_timeserie
from timeseries.timeseriesstub import TimeseriesStub


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
        self.bucket.indraft_fraction = float(bucket_spec['bl f_intrek'])
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
        self.bucket.indraft_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        expected_value = -41302.53
        computed_value = compute_net_drainage(self.bucket, previous_volume)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_g(self):
        """Test compute_net_drainage on more previous day storage than equi storage.

        """
        self.bucket.init_water_level = 0.65
        self.bucket.indraft_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        expected_value = -38352.35
        computed_value = compute_net_drainage(self.bucket, previous_volume)
        self.assertAlmostEqual(expected_value, computed_value, 2)

    def test_h(self):
        """Test compute returns the correct water level.

        """
        self.bucket.indraft_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        evaporation = 20
        precipitation = 5
        seepage = 10

        expected_storage = 413025.34
        result_tuple = compute(self.bucket, previous_volume, evaporation,
                               precipitation, seepage)
        self.assertAlmostEqual(expected_storage, result_tuple[0])

    def test_i(self):
        """Test compute returns the correct flow off.

        """
        self.bucket.equi_water_level = 0.50
        self.bucket.indraft_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        evaporation = 20
        precipitation = 5
        seepage = 10

        expected_flow_off = -655677.73
        result_tuple = compute(self.bucket, previous_volume, evaporation,
                               precipitation, seepage)
        self.assertAlmostEqual(expected_flow_off, result_tuple[1], 2)

    def test_j(self):
        """Test compute returns the correct net drainage.

        """
        self.bucket.equi_water_level = 0.50
        self.bucket.indraft_fraction = 0.04
        previous_volume = self.bucket.init_water_level * self.bucket.surface
        evaporation =  20
        precipitation = 5
        seepage = 10

        expected_drainage = -41302.53
        result_tuple = compute(self.bucket, previous_volume, evaporation,
                               precipitation, seepage)
        self.assertAlmostEqual(expected_drainage, result_tuple[2], 2)

    def test_k(self):
        """Test compute_timeseries starts with the correct initial water volume."""
        today = datetime(2010,12,2)
        evaporation = TimeseriesStub()
        evaporation.add_value(today, 20)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        seepage = TimeseriesStub()
        seepage.add_value(today, 10)
        mock = Mock({"compute": (0, 0, 0, 0, 0)})
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
        evaporation = TimeseriesStub()
        evaporation.add_value(today, 20)
        evaporation.add_value(tomorrow, 30)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        seepage = TimeseriesStub()
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        mock = Mock({"compute": (0, 0, 0, 0, 0)})
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
        evaporation = TimeseriesStub()
        evaporation.add_value(today, 20)
        evaporation.add_value(tomorrow, 30)
        precipitation = TimeseriesStub()
        precipitation.add_value(today, 5)
        precipitation.add_value(tomorrow, 10)
        seepage = TimeseriesStub()
        seepage.add_value(today, 10)
        seepage.add_value(tomorrow, 20)
        mock = Mock({"compute": (0, 0, 0, 0, 0)})
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


class NetIntakeTests(TestCase):
    """Contains tests for the net intake computation of an OpenWater.

    The function compute.retrieve_net_intake computes the net intake of water
    of an OpenWater. To do so, it uses the methods of an OpenWater that
    retrieve all the time series associated with its intakes and its pumps. The
    tests in this test suite override these methods to test the behavior of
    compute.retrieve_net_intake.

    """
    def test_a(self):
        """Test the case without any intake or pump time series."""
        incoming_timeseries = []
        outgoing_timeseries = []
        open_water = OpenWater()
        open_water.retrieve_incoming_timeseries = lambda : incoming_timeseries
        open_water.retrieve_outgoing_timeseries = lambda : outgoing_timeseries
        net_intake = retrieve_net_intake(open_water)
        self.assertEqual(0, len(list(net_intake.events())))

    def test_b(self):
        """Test the case with one intake and one pump time series."""
        incoming_timeseries = [TimeseriesStub((datetime(2010, 12, 15), 10))]
        outgoing_timeseries = [TimeseriesStub((datetime(2010, 12, 15), 2))]
        open_water = OpenWater()
        open_water.retrieve_incoming_timeseries = lambda : incoming_timeseries
        open_water.retrieve_outgoing_timeseries = lambda : outgoing_timeseries
        net_intake = retrieve_net_intake(open_water)
        expected_events = TimeseriesStub((datetime(2010, 12, 15), 8)).events()
        self.assertEqual(list(expected_events), list(net_intake.events()))

    def test_c(self):
        """Test the case with only two pump time series."""
        incoming_timeseries = []
        outgoing_timeseries = [
            TimeseriesStub((datetime(2010, 12, 15), 0)),
            TimeseriesStub((datetime(2010, 12, 16), 10))]
        open_water = OpenWater()
        open_water.retrieve_incoming_timeseries = lambda : incoming_timeseries
        open_water.retrieve_outgoing_timeseries = lambda : outgoing_timeseries
        net_intake = retrieve_net_intake(open_water)
        expected_events = ((datetime(2010, 12, 15), 0),
                           (datetime(2010, 12, 16), -10))
        self.assertEqual(list(expected_events), list(net_intake.events()))


class OpenWaterAccessToPumpingStationsTests(TestCase):
    """Contains tests for the access of an OpenWater to its PumpingStation(s).

    An OpenWater does not have direct access to the time series associated with
    its intakes and pumps: it has to retrieve them via its pumping
    stations. The tests in this test suite supply the OpenWater with dummy
    pumping stations. Then it computes the net intake to test wether the
    OpenWater accesses its pumping stations correctly.

    """
    def test_a(self):
        """Test the case with one intake time series.

        The test defines one pumping station.

        """
        incoming_timeseries = TimeseriesStub((datetime(2010, 12, 15), 10))
        pumping_stations = [PumpingStation()]
        pumping_stations[0].into = True
        pumping_stations[0].retrieve_sum_timeseries = lambda : incoming_timeseries
        open_water = OpenWater()
        open_water.retrieve_pumping_stations = lambda : pumping_stations
        net_intake = retrieve_net_intake(open_water)
        expected_events = ((datetime(2010, 12, 15), 10),)
        self.assertEqual(list(expected_events), list(net_intake.events()))

    def test_b(self):
        """Test the case with one pump time series.

        The test defines one pumping station.

        """
        outgoing_timeseries = TimeseriesStub((datetime(2010, 12, 15), 10))
        pumping_stations = [PumpingStation()]
        pumping_stations[0].into = False
        pumping_stations[0].retrieve_sum_timeseries = lambda : outgoing_timeseries
        open_water = OpenWater()
        open_water.retrieve_pumping_stations = lambda : pumping_stations
        net_intake = retrieve_net_intake(open_water)
        expected_events = ((datetime(2010, 12, 15), -10),)
        self.assertEqual(list(expected_events), list(net_intake.events()))

    def test_c(self):
        """Test the case with one intake and one pump timeseries."""
        incoming_timeseries = TimeseriesStub((datetime(2010, 12, 15), 10))
        outgoing_timeseries = TimeseriesStub((datetime(2010, 12, 16), 5))
        pumping_stations = [PumpingStation() for index in range(0, 2)]
        pumping_stations[0].into = True
        pumping_stations[0].retrieve_sum_timeseries = lambda : incoming_timeseries
        pumping_stations[1].into = False
        pumping_stations[1].retrieve_sum_timeseries = lambda : outgoing_timeseries
        open_water = OpenWater()
        open_water.retrieve_pumping_stations = lambda : pumping_stations
        net_intake = retrieve_net_intake(open_water)
        expected_events = ((datetime(2010, 12, 15), 10),
                           (datetime(2010, 12, 16), -5))
        self.assertEqual(list(expected_events), list(net_intake.events()))

    def test_d(self):
        """Test the case with multiple intake time series.

        The test defines multiple pumping stations for the multiple intake time
        series.

        """
        incoming_timeseries = TimeseriesStub((datetime(2010, 12, 15), 10))
        pumping_stations = [PumpingStation() for index in range(0, 2)]
        pumping_stations[0].into = True
        pumping_stations[0].retrieve_sum_timeseries = lambda : incoming_timeseries
        pumping_stations[1].into = True
        pumping_stations[1].retrieve_sum_timeseries = lambda : incoming_timeseries
        open_water = OpenWater()
        open_water.retrieve_pumping_stations = lambda : pumping_stations
        net_intake = retrieve_net_intake(open_water)
        expected_events = ((datetime(2010, 12, 15), 20),)
        self.assertEqual(list(expected_events), list(net_intake.events()))


class PumpingStationAccessToPumpLinesTests(TestCase):
    """Contains tests for the access of a PumpingStation to its PumpLine(s).

    A PumpingStation does not have direct access to the time series associated
    with its PumpLine(s): it has to retrieve them via the PumpLine(s). The
    tests in this suite supply a PumpingStation with one or more stub
    PumpLine(s). Then it queries the PumpingStation for the time series to test
    wether it accesses its PumpLine(s) correctly.

    """
    def test_a(self):
        """Test the case with one pump line."""
        timeseries = [TimeseriesStub((datetime(2010, 12, 17), 10))]
        pump_lines = [PumpLine()]
        pump_lines[0].retrieve_timeseries = lambda : timeseries[0]
        pumping_station = PumpingStation()
        pumping_station.retrieve_pump_lines = lambda : pump_lines
        timeseries = pumping_station.retrieve_sum_timeseries()
        expected_timeseries = TimeseriesStub((datetime(2010, 12, 17), 10))
        self.assertEqual(expected_timeseries, timeseries)

    def test_b(self):
        """Test the case with multiple pump lines."""
        timeseries = [TimeseriesStub((datetime(2010, 12, 17), 10)),
                      TimeseriesStub((datetime(2010, 12, 17), 20))]
        pump_lines = [PumpLine() for index in range(0, 2)]
        pump_lines[0].retrieve_timeseries = lambda : timeseries[0]
        pump_lines[1].retrieve_timeseries = lambda : timeseries[1]
        pumping_station = PumpingStation()
        pumping_station.retrieve_pump_lines = lambda : pump_lines
        timeseries = pumping_station.retrieve_sum_timeseries()
        expected_timeseries = TimeseriesStub((datetime(2010, 12, 17), 30))
        self.assertEqual(expected_timeseries, timeseries)


def create_saveable_openwater():
    """Return an OpenWater that can be saved to the database.

    When you manually create an OpenWater, you have to fill in all the required
    fields before you can save it to the database. This function creates a
    OpenWater, fills in the required fields and returns it.

    """
    open_water = OpenWater()
    open_water.surface = 0
    open_water.crop_evaporation_factor = 0.0
    open_water.init_water_level = 0.0
    open_water.bottom_height = 0.0
    return open_water

def create_saveable_bucket():
    """Return a bucket that can be saved to the database.

    When you manually create a Bucket, you have to fill in all the required
    fields before you can save it to the database. This function creates a
    Bucket, fills in the required fields and returns it.

    Why would we want to be able to save the bucket to the database? We want to
    use the Bucket as the key in a dictionary which requires Bucket.__eq__ to
    function properly. That function assumes the pk value of the Bucket is set,
    which is set when the Bucket is saved to the database.

    """
    bucket = Bucket()
    bucket.surface_type = Bucket.UNDRAINED_SURFACE
    bucket.surface = 100
    bucket.porosity = 1.0
    bucket.crop_evaporation_factor = 1.0
    bucket.min_crop_evaporation_factor = 1.0
    bucket.drainage_fraction = 1.0
    bucket.indraft_fraction = 1.0
    bucket.init_water_level =  1.0
    bucket.equi_water_level =  1.0
    bucket.min_water_level =  1.0
    bucket.max_water_level =  1.0
    bucket.external_discharge = 1.0
    bucket.upper_porosity = 1.0
    bucket.upper_crop_evaporation_factor = 1.0
    bucket.upper_min_crop_evaporation_factor = 1.0
    bucket.upper_drainage_fraction = 1.0
    bucket.upper_indraft_fraction = 1.0
    return bucket

class BucketSummarizerTests(TestCase):
    """Contains tests for the daily incoming volume computation of an OpenWater.

    """
    def test_a(self):
        """Test the flow off is zero when there are no buckets."""
        bucket = Bucket()
        bucket.surface_type = Bucket.UNDRAINED_SURFACE
        bucket2daily_outcome = {}
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertEqual(0.0, summarizer.compute_sum_undrained_flow_off())

    def test_b(self):
        """Test the flow off in case of one bucket of the right type."""
        bucket = Bucket()
        bucket.surface_type = Bucket.UNDRAINED_SURFACE
        flow_off = -10.0
        net_drainage = 0.0 # don't care for this test
        bucket2daily_outcome = {bucket: [flow_off, net_drainage]}
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertAlmostEqual(-10.0, summarizer.compute_sum_undrained_flow_off())

    def test_c(self):
        """Test the flow off in case of two buckets of the right type."""
        bucket = create_saveable_bucket()
        bucket.surface_type = Bucket.UNDRAINED_SURFACE
        bucket.save()
        another_bucket = create_saveable_bucket()
        another_bucket.surface_type = Bucket.UNDRAINED_SURFACE
        another_bucket.save()
        flow_off = -10.0
        net_drainage = 0.0 # don't care for this test
        bucket2daily_outcome = {bucket: [flow_off, net_drainage],
                                another_bucket: [flow_off, net_drainage]}
        self.assertEqual(2, len(bucket2daily_outcome.keys()))
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertAlmostEqual(-20.0, summarizer.compute_sum_undrained_flow_off())

    def test_d(self):
        """Test the flow off in case of one bucket of the wrong type."""
        bucket = Bucket()
        bucket.surface_type = Bucket.HARDENED_SURFACE
        flow_off = -10.0
        net_drainage = 0.0 # don't care for this test
        bucket2daily_outcome = {bucket: [flow_off, net_drainage]}
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertAlmostEqual(0.0, summarizer.compute_sum_undrained_flow_off())

    def test_aa(self):
        """Test the undrained is zero when there are no buckets."""
        bucket = Bucket()
        bucket.surface_type = Bucket.UNDRAINED_SURFACE
        bucket2daily_outcome = {}
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertAlmostEqual(0.0, summarizer.compute_sum_undrained_net_drainage())

    def test_ab(self):
        """Test the undrained when there is one bucket of the right type."""
        bucket = create_saveable_bucket()
        bucket.surface_type = Bucket.HARDENED_SURFACE
        flow_off = 0.0 # don't care for this test
        net_drainage = -10.0
        bucket2daily_outcome = { bucket: [flow_off, net_drainage] }
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertAlmostEqual(-10.0, summarizer.compute_sum_undrained_net_drainage())

    def test_ac(self):
        """Test the undrained when there is one bucket of the right type with positive net drainage."""
        bucket = create_saveable_bucket()
        bucket.surface_type = Bucket.HARDENED_SURFACE
        flow_off = 0.0 # don't care for this test
        net_drainage = 10.0
        bucket2daily_outcome = { bucket: [flow_off, net_drainage] }
        summarizer = BucketSummarizer(bucket2daily_outcome)
        self.assertAlmostEqual(0.0, summarizer.compute_sum_undrained_net_drainage())

class TimeseriesRetrieverStub():

    def __init__(self):
        self.precipitation = TimeseriesStub()
        self.evaporation = TimeseriesStub()
        self.seepage = TimeseriesStub()

    def get_timeseries(self, name, start_date, end_date):
        return getattr(self, name)


class WaterbalanceComputerTests(TestCase):

    def setUp(self):
        self.buckets_result = {} # don't care
        self.buckets_computer = Mock({"compute": self.buckets_result})
        self.level_result = [TimeseriesStub(),
                             TimeseriesStub(),
                             TimeseriesStub(),
                             TimeseriesStub()] # don't care
        self.level_control_computer = Mock({"compute": self.level_result})
        self.buckets = [Bucket(), Bucket()]
        self.area = WaterbalanceArea()
        self.area.open_water = create_saveable_openwater()
        self.area.open_water.retrieve_minimum_level = lambda : TimeseriesStub()
        self.area.open_water.retrieve_maximum_level = lambda : TimeseriesStub()
        self.area.retrieve_buckets = lambda : self.buckets
        self.precipitation = TimeseriesStub()
        self.evaporation = TimeseriesStub()
        self.seepage = TimeseriesStub()
        self.area.retrieve_precipitation = lambda s, e: self.precipitation
        self.area.retrieve_evaporation = lambda s, e: self.evaporation
        self.area.retrieve_seepage = lambda s, e: self.seepage

    def test_a(self):
        """Test that compute calls the right method of the bucket computer."""
        start = datetime(2010, 12, 21)
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.level_control_storage = Mock()
        computer.compute(self.area, start, start + timedelta(1))
        calls = self.buckets_computer.getAllCalls()
        self.assertEqual(1, len(calls))
        self.assertEqual("compute", calls[0].getName())

    def test_b(self):
        """Test that method compute passes the buckets of the waterbalance area to the bucket computer."""
        start = datetime(2010, 12, 21)
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.level_control_storage = Mock()
        computer.compute(self.area, start, start + timedelta(1))
        calls = self.buckets_computer.getNamedCalls("compute")
        self.assertEqual(self.buckets, calls[0].getParam(0))

    def test_c(self):
        """Test that method compute passes the time series to the bucket computer."""
        start = datetime(2010, 12, 21)
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.level_control_storage = Mock()
        computer.compute(self.area, start, start + timedelta(1))
        calls = self.buckets_computer.getNamedCalls("compute")
        self.assertEqual(self.precipitation, calls[0].getParam(1))
        self.assertEqual(self.evaporation, calls[0].getParam(2))
        self.assertEqual(self.seepage, calls[0].getParam(3))

    def test_d(self):
        """Test that method compute returns the bucket time series."""
        start = datetime(2010, 12, 21)
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.level_control_storage = Mock()
        result = computer.compute(self.area, start, start + timedelta(1))
        self.assertEqual(self.buckets_result, result[0])

    def test_e(self):
        """Test that method compute returns the level control time series."""
        start = datetime(2010, 12, 21)
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.level_control_storage = Mock()
        result = computer.compute(self.area, start, start + timedelta(1))
        self.assertEqual(self.level_result, result[1])

    def test_f(self):
        """Test that method compute stores the undrained time series of the buckets summary.

        This test does not check that the time series are stored in the
        database.

        """
        buckets_summary = BucketsSummary()
        today = datetime(2011, 1, 23)
        buckets_summary.undrained = TimeseriesStub((today, 10))
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.buckets_summarizer = Mock({"compute": buckets_summary})
        computer.level_control_storage = Mock()
        result = computer.compute(self.area, today, today + timedelta(1))
        result # to silence pyflakes
        wb_timeserie = self.area.open_water.undrained
        self.assertEqual(list(buckets_summary.undrained.events()), list(wb_timeserie.volume.events()))

    def test_g(self):
        """Test that method compute stores the undrained time series of the buckets summary.

        This test checks that the time series are stored in the database.

        """
        buckets_summary = BucketsSummary()
        today = datetime(2011, 1, 23)
        buckets_summary.undrained = TimeseriesStub((today, 10))
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.buckets_summarizer = Mock({"compute": buckets_summary})
        computer.level_control_storage = Mock()
        result = computer.compute(self.area, today, today + timedelta(1))
        result # to silence pyflakes

        pk = self.area.open_water.undrained.pk

        wb_timeserie = WaterbalanceTimeserie.objects.get(pk=pk)
        self.assertEqual(list(buckets_summary.undrained.events()), list(wb_timeserie.volume.events()))

        pk_open_water = self.area.open_water.pk
        open_water = OpenWater.objects.get(pk=pk_open_water)
        self.assertEqual(pk, open_water.undrained.pk)

    def test_h(self):
        """Test that method compute removes the existing undrained time series of the buckets summary.

        This test checks that the time series are stored in the database.

        """
        buckets_summary = BucketsSummary()
        today = datetime(2011, 1, 23)
        buckets_summary.undrained = TimeseriesStub((today, 10))
        computer = WaterbalanceComputer(self.buckets_computer,
                                        self.level_control_computer)
        computer.buckets_summarizer = Mock({"compute": buckets_summary})
        computer.level_control_storage = Mock()
        result = computer.compute(self.area, today, today + timedelta(1))
        result # to silence pyflakes

        pk = self.area.open_water.undrained.volume.pk

        result = computer.compute(self.area, today, today + timedelta(1))
        result # to silence pyflakes

        self.assertEqual(0, Timeseries.objects.filter(pk=pk).count())

class StorageTests(TestCase):

    def setUp(self):
        self.area = WaterbalanceArea()
        self.area.retrieve_precipitation = lambda s, e: TimeseriesStub()
        self.area.retrieve_evaporation = lambda s, e: TimeseriesStub()
        self.area.retrieve_seepage = lambda s, e: TimeseriesStub()
        self.area.open_water = create_saveable_openwater()
        self.area.open_water.retrieve_minimum_level = lambda : TimeseriesStub()
        self.area.open_water.retrieve_maximum_level = lambda : TimeseriesStub()

    def test_a(self):
        """Test WaterbalanceComputer.compute creates a storage time series when none exists.

        This test checks that the time series are stored in the database.

        """
        self.assertEqual(None, self.area.open_water.storage)
        today = datetime(2011, 1, 24)
        computer = WaterbalanceComputer()
        x = computer.compute(self.area, today, today + timedelta(1)); x
        pk = self.area.open_water.storage.pk
        self.assertEqual(1, WaterbalanceTimeserie.objects.filter(pk=pk).count())

    def test_b(self):
        """Test WaterbalanceComputer.compute reuses an existing storage time series.

        This test checks that the time series are stored in the database.

        """
        self.assertEqual(None, self.area.open_water.storage)
        today = datetime(2011, 1, 24)
        computer = WaterbalanceComputer()
        x = computer.compute(self.area, today, today + timedelta(1)); x
        pk = self.area.open_water.storage.pk
        x = computer.compute(self.area, today, today + timedelta(1)); x
        self.assertEqual(1, WaterbalanceTimeserie.objects.filter(pk=pk).count())

    def test_c(self):
        """Test WaterbalanceComputer.compute creates a storage volume time series when none exists.

        This test checks that the time series are stored in the database.

        """
        self.assertEqual(None, self.area.open_water.storage)
        today = datetime(2011, 1, 24)
        computer = WaterbalanceComputer()
        x = computer.compute(self.area, today, today + timedelta(1)); x
        pk = self.area.open_water.storage.volume.pk
        self.assertEqual(1, Timeseries.objects.filter(pk=pk).count())

    def test_d(self):
        """Test WaterbalanceComputer.compute recreates an existing storage volume time series.

        This test checks that the time series are stored in the database.

        """
        self.assertEqual(None, self.area.open_water.storage)
        today = datetime(2011, 1, 24)
        computer = WaterbalanceComputer()
        x = computer.compute(self.area, today, today + timedelta(1)); x
        pk = self.area.open_water.storage.volume.pk
        x = computer.compute(self.area, today, today + timedelta(1)); x
        self.assertEqual(0, Timeseries.objects.filter(pk=pk).count())

class TotalDailyBucketOutcomeTests(TestCase):

    def test_a(self):
        """When there are no buckets, there is no total daily bucket outcome."""
        bucket2outcome = {}
        for outcome in total_daily_bucket_outcome(bucket2outcome):
            self.assertFalse(True)

    def test_b(self):
        """Test the case that there is a single bucket."""
        bucket = create_saveable_bucket()
        bucket.save()
        outcome = BucketOutcome()
        outcome.flow_off.add_value(datetime(2011, 1, 11), 10.0)
        outcome.flow_off.add_value(datetime(2011, 1, 12), 20.0)
        outcome.net_drainage.add_value(datetime(2011, 1, 11), 30.0)
        outcome.net_drainage.add_value(datetime(2011, 1, 12), 40.0)
        bucket2outcome = {bucket: outcome}
        outcomes = list(total_daily_bucket_outcome(bucket2outcome))

        number_of_days = 2
        self.assertEqual(number_of_days, len(outcomes))
        self.assertEqual(datetime(2011, 1, 11), outcomes[0][0])
        self.assertEqual(datetime(2011, 1, 12), outcomes[1][0])

        number_of_buckets = 1
        self.assertEqual(number_of_buckets, len(outcomes[0][1].items()))
        self.assert_(bucket in outcomes[0][1].keys())
        self.assertEqual(number_of_buckets, len(outcomes[1][1].items()))
        self.assert_(bucket in outcomes[1][1].keys())

        event_values = outcomes[0][1][bucket]
        self.assertEqual(10.0, event_values[0])
        self.assertEqual(30.0, event_values[1])
        event_values = outcomes[1][1][bucket]
        self.assertEqual(20.0, event_values[0])
        self.assertEqual(40.0, event_values[1])

    def test_c(self):
        """Test the case that there are two buckets."""
        bucket2outcome = {}
        bucket0 = create_saveable_bucket()
        bucket0.save()
        outcome = BucketOutcome()
        outcome.flow_off.add_value(datetime(2011, 1, 11), 10.0)
        outcome.flow_off.add_value(datetime(2011, 1, 12), 20.0)
        outcome.net_drainage.add_value(datetime(2011, 1, 11), 30.0)
        outcome.net_drainage.add_value(datetime(2011, 1, 12), 40.0)
        bucket2outcome[bucket0] = outcome
        bucket1 = create_saveable_bucket()
        bucket1.save()
        outcome = BucketOutcome()
        outcome.flow_off.add_value(datetime(2011, 1, 11), 50.0)
        outcome.flow_off.add_value(datetime(2011, 1, 12), 60.0)
        outcome.net_drainage.add_value(datetime(2011, 1, 11), 70.0)
        outcome.net_drainage.add_value(datetime(2011, 1, 12), 80.0)
        bucket2outcome[bucket1] = outcome
        outcomes = list(total_daily_bucket_outcome(bucket2outcome))

        number_of_days = 2
        self.assertEqual(number_of_days, len(outcomes))
        self.assertEqual(datetime(2011, 1, 11), outcomes[0][0])
        self.assertEqual(datetime(2011, 1, 12), outcomes[1][0])

        number_of_buckets = 2
        self.assertEqual(number_of_buckets, len(outcomes[0][1].items()))
        self.assert_(bucket0 in outcomes[0][1].keys())
        self.assert_(bucket1 in outcomes[0][1].keys())
        self.assertEqual(number_of_buckets, len(outcomes[1][1].items()))
        self.assert_(bucket0 in outcomes[1][1].keys())
        self.assert_(bucket1 in outcomes[1][1].keys())

        self.assertEqual([10.0, 30.0], outcomes[0][1][bucket0])
        self.assertEqual([20.0, 40.0], outcomes[1][1][bucket0])
        self.assertEqual([50.0, 70.0], outcomes[0][1][bucket1])
        self.assertEqual([60.0, 80.0], outcomes[1][1][bucket1])

class RetrieveIntakesTimeseriesTests(TestCase):

    def test_a(self):
        "Test when there are no intakes and no pumps."""
        open_water = create_saveable_openwater()

        waterbalance_computer = WaterbalanceComputer()
        intakes, intakes_timeseries = \
                 waterbalance_computer.retrieve_intakes_timeseries(open_water)

        self.assertEqual([], intakes)
        self.assertEqual([], intakes_timeseries)

    def test_b(self):
        """Test when there is a single intake.

        The intake cannot be used for level control.
        """
        open_water = create_saveable_openwater()
        open_water.save()
        intake = PumpingStation()
        intake.open_water = open_water
        intake.name = "Inlaat Vecht"
        intake.into = True
        intake.computed_level_control = False
        intake.percentage = 100 # don't care but obligatory
        intake.save()

        waterbalance_computer = WaterbalanceComputer()
        intakes, intakes_timeseries = \
                 waterbalance_computer.retrieve_intakes_timeseries(open_water)

        self.assertEqual([intake.pk], [intake.pk for intake in intakes])

    def test_c(self):
        """Test when there is a single intake.

        The intake can be used for level control.
        """
        open_water = create_saveable_openwater()
        open_water.save()
        intake = PumpingStation()
        intake.open_water = open_water
        intake.name = "Inlaat Vecht"
        intake.into = True
        intake.computed_level_control = True
        intake.percentage = 100 # don't care but obligatory
        intake.save()
        timeseries = TimeseriesStub((datetime(2011, 2, 1), 10.0))
        store_waterbalance_timeserie(intake, "level_control", timeseries)
        intake.save()

        waterbalance_computer = WaterbalanceComputer()
        intakes, intakes_timeseries = \
                 waterbalance_computer.retrieve_intakes_timeseries(open_water)

        self.assertEqual([intake.pk], [intake.pk for intake in intakes])
        self.assertEqual([timeseries], intakes_timeseries)



