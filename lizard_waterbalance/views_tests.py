from datetime import datetime
from unittest import TestCase

from lizard_waterbalance.views import move_forward
from lizard_waterbalance.views import insert_restart


class Tests(TestCase):

    def test_a(self):
        """Test everything is moved forward by almost one day."""
        times = [datetime(2011, 4, 4), datetime(2011, 4, 5)]
        expected_times = [datetime(2011, 4, 4, 23, 59, 59),
                          datetime(2011, 4, 5, 23, 59, 59)]
        self.assertEqual(expected_times, move_forward(times, 'day'))

    def test_b(self):
        """Test everything is moved forward by almost one month."""
        times = [datetime(2011, 4, 1), datetime(2011, 5, 1)]
        expected_times = [datetime(2011, 4, 30, 23, 59, 59),
                          datetime(2011, 5, 31, 23, 59, 59)]
        self.assertEqual(expected_times, move_forward(times, 'month'))

    def test_c(self):
        """Test everything is moved forward by almost one quarter."""
        times = [datetime(2011, 4, 1), datetime(2011, 7, 1)]
        expected_times = [datetime(2011, 6, 30, 23, 59, 59),
                          datetime(2011, 9, 30, 23, 59, 59)]
        self.assertEqual(expected_times, move_forward(times, 'quarter'))

    def test_d(self):
        """Test everything is moved forward by almost one year."""
        times = [datetime(2011, 4, 1), datetime(2012, 4, 1)]
        expected_times = [datetime(2012, 3, 31, 23, 59, 59),
                          datetime(2013, 3, 31, 23, 59, 59)]
        self.assertEqual(expected_times, move_forward(times, 'year'))

    def test_e(self):
        """Test insertion of zero value after the first event of the year."""
        times = [datetime(2010, 9, 30),
                 datetime(2010, 10, 31)]
        values = [10.0, 5.0]
        expected_times = [datetime(2010, 9, 30),
                          datetime(2010, 10, 1),
                          datetime(2010, 10, 31)]
        expected_values = [10.0, 0.0, 5.0]
        times, values = insert_restart(times, values, 'hydro_year')
        self.assertEqual(expected_times, times)
        self.assertEqual(expected_values, values)

    def test_f(self):
        """Test insertion of zero value after the first event of the year."""
        times = [datetime(2010, 12, 31),
                 datetime(2011, 1, 31)]
        values = [10.0, 5.0]
        expected_times = [datetime(2010, 12, 31),
                          datetime(2011, 1, 1),
                          datetime(2011, 1, 31)]
        expected_values = [10.0, 0.0, 5.0]
        times, values = insert_restart(times, values, 'year')
        self.assertEqual(expected_times, times)
        self.assertEqual(expected_values, values)

    def test_g(self):
        """Test insertion of zero value after the first event of the month."""
        times = [datetime(2011, 4, 30),
                 datetime(2011, 5, 31)]
        values = [10.0, 10.0]
        expected_times = [datetime(2011, 4, 30),
                          datetime(2011, 5, 1),
                          datetime(2011, 5, 31)]
        expected_values = [10.0, 0.0, 10.0]
        times, values = insert_restart(times, values, 'month')
        self.assertEqual(expected_times, times)
        self.assertEqual(expected_values, values)
