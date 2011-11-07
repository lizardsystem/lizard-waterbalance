from datetime import datetime
from unittest import TestCase

from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from dbmodel.models import PumpingStation
from lizard_waterbalance.models import Label
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceScenario
from lizard_waterbalance.localmock import Mock
from lizard_waterbalance.views import CacheKeyName
from lizard_waterbalance.views import DataForCumulativeGraph
from lizard_waterbalance.views import LegendInfo
from lizard_waterbalance.views import raw_add_timeseries
from lizard_waterbalance.views import retrieve_viewable_configurations
from timeseries.timeseriesstub import TimeseriesStub


class DataForCumulativeGraphTests(TestCase):

    def test_a(self):
        """Test everything is moved forward by almost one day."""
        dates, values = [datetime(2011, 4, 4), datetime(2011, 4, 5)], []
        # values do not care for this test
        expected_dates = [datetime(2011, 4, 4, 23, 59, 59),
                          datetime(2011, 4, 5, 23, 59, 59)]
        data = DataForCumulativeGraph(dates, values)
        self.assertEqual(expected_dates, data.move_forward(dates, 'day'))

    def test_b(self):
        """Test everything is moved forward by almost one month."""
        dates, values = [datetime(2011, 4, 1), datetime(2011, 5, 1)], []
        # values do not care for this test
        expected_dates = [datetime(2011, 4, 30, 23, 59, 59),
                          datetime(2011, 5, 31, 23, 59, 59)]
        data = DataForCumulativeGraph(dates, values)
        self.assertEqual(expected_dates, data.move_forward(dates, 'month'))

    def test_c(self):
        """Test everything is moved forward by almost one quarter."""
        dates, values = [datetime(2011, 4, 1), datetime(2011, 7, 1)], []
        # values do not care for this test
        expected_dates = [datetime(2011, 6, 30, 23, 59, 59),
                          datetime(2011, 9, 30, 23, 59, 59)]
        data = DataForCumulativeGraph(dates, values)
        self.assertEqual(expected_dates, data.move_forward(dates, 'quarter'))

    def test_d(self):
        """Test everything is moved forward by almost one year."""
        dates, values = [datetime(2011, 4, 1), datetime(2012, 4, 1)], []
        # values do not care for this test
        expected_dates = [datetime(2012, 3, 31, 23, 59, 59),
                          datetime(2013, 3, 31, 23, 59, 59)]
        data = DataForCumulativeGraph(dates, values)
        self.assertEqual(expected_dates, data.move_forward(dates, 'year'))

    def test_e(self):
        """Test insert of a reset as the first event of the hydrological year.

        """
        dates = [datetime(2010, 9, 30), datetime(2010, 10, 31)]
        values = [10.0, 5.0]
        expected_dates = [datetime(2010, 9, 30),
                          datetime(2010, 10, 1),
                          datetime(2010, 10, 31)]
        expected_values = [10.0, 0.0, 5.0]
        data = DataForCumulativeGraph(dates, values)
        dates, values = data.insert_restart(dates, values, 'hydro_year')
        self.assertEqual(expected_dates, dates)
        self.assertEqual(expected_values, values)

    def test_f(self):
        """Test insert of a reset as the first event of the year."""
        dates = [datetime(2010, 12, 31), datetime(2011, 1, 31)]
        values = [10.0, 5.0]
        expected_dates = [datetime(2010, 12, 31),
                          datetime(2011, 1, 1),
                          datetime(2011, 1, 31)]
        expected_values = [10.0, 0.0, 5.0]
        data = DataForCumulativeGraph(dates, values)
        dates, values = data.insert_restart(dates, values, 'year')
        self.assertEqual(expected_dates, dates)
        self.assertEqual(expected_values, values)

    def test_g(self):
        """Test insert of a reset as the first event of the quarter."""
        dates = [datetime(2010, 9, 30), datetime(2010, 10, 31)]
        values = [10.0, 5.0]
        expected_dates = [datetime(2010, 9, 30),
                          datetime(2010, 10, 1),
                          datetime(2010, 10, 31)]
        expected_values = [10.0, 0.0, 5.0]
        data = DataForCumulativeGraph(dates, values)
        dates, values = data.insert_restart(dates, values, 'quarter')
        self.assertEqual(expected_dates, dates)
        self.assertEqual(expected_values, values)

    def test_h(self):
        """Test insert of a reset as the first event of the month."""
        dates = [datetime(2011, 4, 30), datetime(2011, 5, 31)]
        values = [10.0, 5.0]
        expected_dates = [datetime(2011, 4, 30),
                          datetime(2011, 5, 1),
                          datetime(2011, 5, 31)]
        expected_values = [10.0, 0.0, 5.0]
        data = DataForCumulativeGraph(dates, values)
        dates, values = data.insert_restart(dates, values, 'month')
        self.assertEqual(expected_dates, dates)
        self.assertEqual(expected_values, values)

class CacheKeyNameTests(TestCase):

    def test_a(self):
        """Test the case for a __unicode__ return value without spaces."""
        configuration = Mock({"__unicode__": "hello"})
        cache_key_name = CacheKeyName(configuration)
        self.assertEqual("hello", cache_key_name.configuration_slug)

    def test_b(self):
        """Test the case for a __unicode__ return value with spaces."""
        configuration = Mock({"__unicode__": "hello world"})
        cache_key_name = CacheKeyName(configuration)
        self.assertEqual("hello-world", cache_key_name.configuration_slug)

    def test_c(self):
        """Test method get."""
        configuration = Mock({"__unicode__": "hello world"})
        cache_key_name = CacheKeyName(configuration)
        self.assertEqual("sluice_error::hello-world",
                         cache_key_name.get("sluice_error"))

class LegendInfoTestSuite(TestCase):

    def test_a(self):
        """Test the correct legend name is returned when the key is a string."""
        label = Label()
        label.name = "neerslag"
        label.program_name = "precipitation"
        label.save()
        legend_info = LegendInfo()
        legend_info.retrieve_labels()
        (legend_name, label) = legend_info.retrieve("precipitation")
        self.assertEqual("neerslag", legend_name)
        label.delete()

    def test_b(self):
        """Test the correct Label is returned when the key is a string."""
        label = Label()
        label.name = "neerslag"
        label.program_name = "precipitation"
        label.save()
        stored_label = Label.objects.get(name__iexact="neerslag")
        legend_info = LegendInfo()
        legend_info.retrieve_labels()
        (legend_name, label) = legend_info.retrieve("precipitation")
        self.assertEqual(stored_label.pk, label.pk)
        label.delete()

    def test_c(self):
        """Test the correct legend name is returned when the key is an intake.

        An intake is implemented by a PumpingStation.

        """
        label = Label()
        label.name = "inlaat 1"
        label.program_name = "inlet1"
        label.save()
        intake = PumpingStation(None, None)
        intake.name = "dijklek"
        intake.label = label
        # Note that we do not save the intake to the database. To save a
        # PumpingStation, we need to create a whole tree of objects. But that
        # is not necessary as long as a LegendInfo does not query that part of
        # the database.
        legend_info = LegendInfo()
        legend_info.retrieve_labels()
        (legend_name, label) = legend_info.retrieve(intake)
        self.assertEqual("dijklek", legend_name)
        label.delete()

    def test_d(self):
        """Test the correct legend Label is returned when the key is an intake.

        An intake is implemented by a PumpingStation.

        """
        label = Label()
        label.name = "inlaat 1"
        label.program_name = "inlet1"
        label.save()
        intake = PumpingStation(None, None)
        intake.name = "dijklek"
        intake.label = label
        # Note that we do not save the intake to the database. To save a
        # PumpingStation, we need to create a whole tree of objects. But that
        # is not necessary as long as a LegendInfo does not query that part of
        # the database.
        stored_label = Label.objects.get(name__iexact="inlaat 1")
        legend_info = LegendInfo()
        legend_info.retrieve_labels()
        (legend_name, label) = legend_info.retrieve(intake)
        self.assertEqual(stored_label.pk, label.pk)
        label.delete()

class RawAddTestSuite(TestCase):

    def test_a(self):
        """Test the sum of two empty time series."""
        timeserie_a = TimeseriesStub()
        timeserie_b = TimeseriesStub()
        result = raw_add_timeseries(timeserie_a, timeserie_b)
        self.assertEqual([], list(result.events()))

    def test_b(self):
        """Test the sum of two time series of which the first one is empty."""
        timeserie_a = TimeseriesStub((datetime(2011, 5, 30), 10))
        timeserie_b = TimeseriesStub()
        result = raw_add_timeseries(timeserie_a, timeserie_b)
        self.assertEqual([(datetime(2011, 5, 30), 10)], list(result.events()))

    def test_c(self):
        """Test the sum of two time series of which the second one is empty."""
        timeserie_a = TimeseriesStub()
        timeserie_b = TimeseriesStub((datetime(2011, 5, 30), 10))
        result = raw_add_timeseries(timeserie_a, timeserie_b)
        self.assertEqual([(datetime(2011, 5, 30), 10)], list(result.events()))

    def test_d(self):
        """Test the sum of two non-empty time series."""
        timeserie_a = TimeseriesStub((datetime(2011, 5, 30), 10))
        timeserie_b = TimeseriesStub((datetime(2011, 5, 30), 20))
        result = raw_add_timeseries(timeserie_a, timeserie_b)
        self.assertEqual([(datetime(2011, 5, 30), 30)], list(result.events()))

    def test_e(self):
        """Test the sum of two non-empty time series."""
        timeserie_a = TimeseriesStub((datetime(2011, 5, 30), 10))
        timeserie_b = TimeseriesStub((datetime(2011, 5, 31), 20))
        result = raw_add_timeseries(timeserie_a, timeserie_b)
        self.assertEqual([(datetime(2011, 5, 30), 10), (datetime(2011, 5, 31), 20)], list(result.events()))

    def test_f(self):
        """Test the sum of two non-empty time series."""
        timeserie_a = TimeseriesStub((datetime(2011, 5, 31), 10))
        timeserie_b = TimeseriesStub((datetime(2011, 5, 30), 20))
        result = raw_add_timeseries(timeserie_a, timeserie_b)
        self.assertEqual([(datetime(2011, 5, 30), 20), (datetime(2011, 5, 31), 10)], list(result.events()))


class PermissionTests(TestCase):
    """Implements the tests for function retrieve_viewable_configurations."""

    def setUp(self):
        """Create the database objects required for the tests."""
        self.area = WaterbalanceArea()
        self.area.active = True
        self.area.name = "WaterbalanceArea for PermissionTests"
        self.area.save()
        self.scenario = WaterbalanceScenario()
        self.scenario.active = True
        self.scenario.name = "WaterbalanceScenario for PermissionTests"
        self.scenario.public = True
        self.scenario.save()
        self.configuration = WaterbalanceConf()
        self.configuration.waterbalance_area = self.area
        self.configuration.waterbalance_scenario = self.scenario
        self.configuration.calculation_start_date = datetime(2011, 7, 15)
        self.configuration.calculation_end_date = datetime(2011, 7, 16)
        self.configuration.save()
        self.user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        self.user.save()

    def tearDown(self):
        """Delete the database objects we created for the tests."""
        self.user.delete()
        self.scenario.delete()
        self.area.delete()

    def test_a(self):
        """A user is allowed to view a public scenario.

        The user is not logged in.

        """
        configurations = retrieve_viewable_configurations(AnonymousUser())
        self.assertEqual([self.configuration], list(configurations))

    def test_b(self):
        """A user is not allowed to view a non-public scenario.

        The user is not logged in.

        """
        self.scenario.public = False
        self.scenario.save()

        configurations = retrieve_viewable_configurations(AnonymousUser())
        self.assertEqual([], list(configurations))

    def test_c(self):
        """A user is allowed to view a public scenario.

        The user is logged in.

        """
        user = authenticate(username="john", password="johnpassword")
        assert user is not None

        configurations = retrieve_viewable_configurations(user)
        self.assertEqual([self.configuration], list(configurations))

    def test_d(self):
        """A user is not-allowed to view a non-public scenario.

        The user is logged in.

        """
        self.scenario.public = False
        self.scenario.save()
        user = authenticate(username="john", password="johnpassword")
        assert user is not None

        configurations = retrieve_viewable_configurations(user)
        self.assertEqual([], list(configurations))

    def test_e(self):
        """A user is allowed to view a non-public scenario.

        The user is logged in and has the right to view non-public scenarios.

        """
        self.scenario.public = False
        self.scenario.save()
        permission = Permission.objects.get(codename="see_not_public_scenarios")
        assert permission is not None
        self.user.user_permissions.add(permission)
        self.user.save()
        user = authenticate(username="john", password="johnpassword")
        assert user is not None

        configurations = retrieve_viewable_configurations(user)
        self.assertEqual([self.configuration], list(configurations))

    def test_f(self):
        """A user is not-allowed to view a non-public scenario.

        The user is logged in, has the right to view non-public scenarios but
        is inactive.

        """
        self.scenario.public = False
        self.scenario.save()
        permission = Permission.objects.get(codename="see_not_public_scenarios")
        assert permission is not None
        self.user.user_permissions.add(permission)
        self.user.is_active = False
        self.user.save()
        user = authenticate(username="john", password="johnpassword")
        assert user is not None
        assert not user.is_active

        configurations = retrieve_viewable_configurations(user)
        self.assertEqual([], list(configurations))

