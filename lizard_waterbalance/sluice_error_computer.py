# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

# -*- coding: utf-8 -*-
# pylint: disable=C0111

import logging

from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import multiply_timeseries
from timeseries.timeseriesstub import SparseTimeseriesStub


logger = logging.getLogger(__name__) # pylint: disable=C0103, C0301


class SluiceErrorComputer: # pylint: disable=W0232, R0903
    """Implements the functionality to compute the sluice error."""

    def compute(self, start_date, end_date, level_control_timeseries, # pylint: disable=C0301, R0201
                measured_timeseries):
        """Compute and return the sluice error time series.

        The sluice error on a specific day is defined as the sum of the
        (calculated) level control intakes and pumps values minus the sum of the
        measured (non level control) intakes and pumps values.

        This function returns the sluice error time series as a
        SparseTimeseriesStub.

        Parameters:
          * level_control_timeseries *
            list of calculated time series of the level control intakes and pumps
          * measured_timeseries *
            list of measured time series of the (non level control) intakes and pumps
          * start_date *
            first date for which to compute the sluice error
          * end_date *
            date after the last date for which to compute the sluice error

        """
        sluice_error_timeseries = SparseTimeseriesStub()

        timeseries = level_control_timeseries + \
           [multiply_timeseries(ts, -1.0) for ts in measured_timeseries]
        for date, value in add_timeseries(*timeseries).events(): # pylint: disable=C0301, W0142
            logger.debug("%s, %f", date.isoformat(), value)
            if date < start_date:
                continue
            elif date < end_date:
                sluice_error_timeseries.add_value(date, value)
            else:
                break

        return sluice_error_timeseries
