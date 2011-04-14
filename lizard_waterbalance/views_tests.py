from datetime import datetime
from unittest import TestCase

from mock import Mock

from lizard_waterbalance.views import CacheKeyName
from lizard_waterbalance.views import CachedWaterbalanceComputer
from lizard_waterbalance.views import DataForCumulativeGraph

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
