# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

# -*- coding: utf-8 -*-
# pylint: disable=C0111

import logging

from datetime import datetime
from datetime import timedelta
from unittest import TestCase

from lizard_wbcomputation.sluice_error_computer import SluiceErrorComputer
from timeseries.timeseriesstub import TimeseriesStub

logger = logging.getLogger(__name__) # pylint: disable=C0103, C0301

def stub_empty_timeseries(only_input=False):
    """Return the empty list of volume timeseries.

    This function assumes there is no intake or pump. This means that this
    function can ignore parameter only_input.

    """
    return []

def stuba_retrieve_incoming_timeseries(only_input=False):
    """Return the dictionary of intake to measured time series.

    This function assumes there is a single intake that is not used for level
    control. This means that this function can ignore parameter only_input.

    """
    # We need to construct a dictionary of intake to time series. As we are not
    # interested in the intake, we use the value 0 for the intake even though 0
    # is not a valid PumpingStation. As long as we do not use 0 for an intake,
    # we get away with it.
    return {0: TimeseriesStub((datetime(2011, 3, 9), 8))}

def ts_factory(*args):
    """Return a TimeseriesStub for the given arguments.

    Parameters:
      * arg[0] *
        first date of the time series
      * arg[1:] *
        values of the daily events starting on the first date

    """
    date = args[0]
    ts = TimeseriesStub()
    for arg in args[1:]:
        ts.add_value(date, arg)
        date = date + timedelta(1)
    return ts


def test_ts_factory():
    """Implements a unit test for function ts_factory."""
    ts = ts_factory(datetime(2011, 7, 13), 1.0, 2.0 , 3.0)
    timeseries = TimeseriesStub((datetime(2011, 7, 13), 1.0),
                                (datetime(2011, 7, 14), 2.0),
                                (datetime(2011, 7, 15), 3.0))
    assert ts == timeseries

class SluiceErrorComputerTests(TestCase):
    """Implements unit tests for a SluiceErrorComputer."""

    def test_a(self):
        """Test when there are no level control and measured time series."""
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(datetime(2011, 7, 8),
                                        datetime(2011, 7, 9), [], [])
        self.assertEqual(TimeseriesStub(), sluice_error)

    def test_b(self):
        """Test when level control and measured time series are in balance."""
        computer = SluiceErrorComputer()
        level_control_timeseries = [TimeseriesStub((datetime(2011, 7, 8), 4.0))]
        measured_timeseries = [TimeseriesStub((datetime(2011, 7, 8), 4.0))]
        sluice_error = computer.compute(datetime(2011, 7, 8),
                                        datetime(2011, 7, 9),
                                        level_control_timeseries,
                                        measured_timeseries)
        self.assertEqual(TimeseriesStub((datetime(2011, 7, 8), 0)), sluice_error)

    def test_c(self):
        """Test when level control and measured time series are not in balance."""
        computer = SluiceErrorComputer()
        level_control_timeseries = [TimeseriesStub((datetime(2011, 7, 8), 4.0))]
        measured_timeseries = [TimeseriesStub((datetime(2011, 7, 8), 2.0))]
        sluice_error = computer.compute(datetime(2011, 7, 8),
                                        datetime(2011, 7, 9),
                                        level_control_timeseries,
                                        measured_timeseries)
        self.assertEqual(TimeseriesStub((datetime(2011, 7, 8), 2)), sluice_error)

    def test_d(self):
        """Test when level control and measured time series are not in balance.

        There are multiple events for the level control and measured timeseries.
        """
        date = datetime(2011, 7, 8)
        level_control_timeseries = [ts_factory(date, 4.0, 2.0)]
        measured_timeseries = [ts_factory(date, 3.0, 0.0)]
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(date, date + timedelta(2),
                                        level_control_timeseries,
                                        measured_timeseries)
        self.assertEqual(ts_factory(date, 1.0, 2.0), sluice_error)

    def test_da(self):
        """Test when level control and measured time series are not in balance.

        There are multiple events for the level control and measured
        timeseries. The date of the first event is before the start date.
        """
        today = datetime(2011, 7, 13)
        tomorrow = today + timedelta(1)
        level_control_timeseries = [ts_factory(today, 4.0, 2.0)]
        measured_timeseries = [ts_factory(today, 3.0, 0.0)]
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(tomorrow, tomorrow + timedelta(1),
                                        level_control_timeseries,
                                        measured_timeseries)
        self.assertEqual(ts_factory(tomorrow, 2.0), sluice_error)

    def test_db(self):
        """Test when level control and measured time series are not in balance.

        There are multiple events for the level control and measured
        timeseries. The date of the last event is at the end date.
        """
        today = datetime(2011, 7, 13)
        tomorrow = today + timedelta(1)
        level_control_timeseries = [ts_factory(today, 4.0, 2.0)]
        measured_timeseries = [ts_factory(today, 3.0, 0.0)]
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(today, tomorrow,
                                        level_control_timeseries,
                                        measured_timeseries)
        self.assertEqual(ts_factory(today, 1.0), sluice_error)

    def test_e(self):
        """Test when level control and measured time series are not in balance.

        There are multiple level control and measured timeseries.
        """
        date = datetime(2011, 7, 8)
        tomorrow = date + timedelta(1)
        level_control_timeseries = \
            [ts_factory(date, 4.0), ts_factory(tomorrow, -4.0)]
        measured_timeseries = [ts_factory(date, 3.0), ts_factory(tomorrow, -2.0)]
        computer = SluiceErrorComputer()
        sluice_error = computer.compute(date, tomorrow + timedelta(1),
                                        level_control_timeseries,
                                        measured_timeseries)
        self.assertEqual(ts_factory(date, 1.0, -2.0), sluice_error)
