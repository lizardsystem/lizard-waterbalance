from datetime import datetime
from datetime import timedelta
from unittest import TestCase


def move_back(times, period):
    if period == 'day':
        result = [time - timedelta(1) for time in times]
    elif period == 'month':
        result = []
        for time in times:
            if time.month > 1:
                month = time.month - 1
                year = time.year
            else:
                month = 12
                year = time.year -1
                result.append(datetime(year, month, time.day))
    return result

class Tests(TestCase):

    def test_a(self):
        """Test everything is moved back by one day"""
        times = [datetime(2011, 4, 4), datetime(2011, 4, 5)]
        expected_times = [datetime(2011, 4, 3), datetime(2011, 4, 4)]
        self.assertEqual(expected_times, move_back(times, 'day'))

    # def test_b(self):
    #     """Test everything is moved back by one month"""
    #     times = [datetime(2011, 4, 1), datetime(2011, 5, 1)]
    #     expected_times = [datetime(2011, 3, 1), datetime(2011, 4, 1)]
    #     self.assertEqual(expected_times, move_back(times, 'month'))

