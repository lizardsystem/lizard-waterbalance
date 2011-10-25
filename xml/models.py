#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The xml package provides the functionality to create from XML files the
# configuration that is required by the computational core of the lizard
# waterbalance Django app
#
# Copyright (C) 2011 Nelen & Schuurmans
#
# This package is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this package.  If not, see <http://www.gnu.org/licenses/>.

class Area(object):
    """Represents the area for which to compute a waterbalance.

    An Area combines attributes of multiple lizard_waterbalance models,
    viz. WaterbalanceConf and OpenWater. We tried to let the Area interface
    mimic the interfaces of those two models.

    Apart from its methods, this object should define the following values:

      - *code*
        string to uniquely identify the current area
      - *name*
        string to easily recognize the current area
      - *surface*
        surface of the open water in (integer) [m2]
      - *bottom_height*
        height of the bottom of the open water in (real) [mNAP]
      - *use_min_max_level_relative_to_meas*
        True if and only if the waterbalance computation should use the
        (real) minimum and maximum water level
      - *waterlevel_measurement*
        timeseries of the measured water level
      - *min_level_relative_to_measurement*
        minimum water level in (real) [mNAP] relative to the time series of the
        measured water level
      - *max_level_relative_to_measurement*
        maximum water level in (real) [mNAP] relative to the time series of the
        measured water level
      - *minimum_level*
        time series of the minimum water level
      - *maximum_level*
        time series of the maximum water level
      - *init_water_level*
        initial water level in (real) [mNAP]
      - *nutricalc_min*
        time series of the minimum nutricalc
      - *nutricalc_incr*
        time series of the minimum nutricalc

    """

    def retrieve_buckets(self):
        """Return the buckets.

        This method comes from lizard_waterbalance.WaterbalanceConf and is used
        in lizard_waterbalance.compute.

        """
        pass

    def retrieve_sobek_buckets(self):
        """Return the buckets whose outcome is predefined.

        This method comes from lizard_waterbalance.WaterbalanceConf and is used
        in lizard_waterbalance.compute.

        """
        pass

    def retrieve_precipitation(self, start_date, end_date):
        """Return the time series that specifies the precipitation.

        Parameters:
          *start_date*
            first date of the returned time series
          *end_date*
            first date after the last date of the returned time series

        This method comes from lizard_waterbalance.WaterbalanceConf and is used
        in lizard_waterbalance.compute.

        """
        pass

    def retrieve_evaporation(self, start_date, end_date):
        """Return the time series that specifies the evaporation.

        Parameters:
          *start_date*
            first date of the returned time series
          *end_date*
            first date after the last date of the returned time series

        This method comes from lizard_waterbalance.WaterbalanceConf and is used
        in lizard_waterbalance.compute.
        """
        pass

    def retrieve_seepage(self, start_date, end_date):
        """Return the time series that specifies the seepage.

        Parameters:
          *start_date*
            first date of the returned time series
          *end_date*
            first date after the last date of the returned time series

        This method comes from lizard_waterbalance.WaterbalanceConf and is used
        in lizard_waterbalance.compute.
        """
        pass


    def retrieve_incoming_timeseries(self):
        """Return the dict of intake to its discharge time series."""
        pass


    def retrieve_outgoing_timeseries(self):
        """Return the dict of pump to its discharge time series."""
        pass

    def retrieve_sewer(self, start_date, end_date):
        """Return the time series of sewer.

        Parameters:
          *start_date*
            first date of the returned time series
          *end_date*
            date after the last date of the returned time series

        """
        pass

    def retrieve_minimum_level(self, start_date, end_date):
        """Return the time series of the minimum water level

        Parameters:
          *start_date*
            first date of the returned time series of the sewer
          *end_date*
            date after the last date of the returned time series of the sewer

        """
        pass

    def retrieve_maximum_level(self, start_date, end_date):
        """Return the time series of the maximum water level

        Parameters:
          *start_date*
            first date of the returned time series of the sewer
          *end_date*
            date after the last date of the returned time series of the sewer

        """
        pass

    def retrieve_pumping_stations(self):
        """Return the pumping stations."""
        pass
