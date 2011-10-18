#!/usr/bin/python
# -*- coding: utf-8 -*-

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

    """

    def retrieve_buckets(self):
        """Return the buckets."""
        pass

    def retrieve_sobek_buckets(self):
        """Return the buckets whose outcome is predefined."""
        pass

    def retrieve_precipitation(self):
        """Return the time series that specifies the precipitation."""
        pass

    def retrieve_evaporation(self):
        """Return the time series that specifies the evaporation."""
        pass

    def retrieve_seepage(self):
        """Return the time series that specifies the seepage."""
        pass

    def save(self):
        pass

    def __unicode__(self):
        pass

    def calculation_start_date(self):
        """Return the first date for which the waterbalance should be computed.

        """
        pass

    def calculation_end_date(self):
        """Return the last date for which the waterbalance should be computed.

        """
        pass

    def get_all_config_concentrations(self):
        pass

    def nutricalc_minima_exists(self):
        """Return whether a minimum time series for nutricalc is defined.

        """
        pass

    def retrieve_nutricalc_minima(self):
        """Return the minimum time series for nutricalc."""
        pass

    def nutricalc_increments_exists(self):
        """Return whether an incremental time series for nutricalc is defined.

        """
        pass

    def retrieve_nutricalc_increments(self):
        """Return the incremental time series for nutricalc."""
        pass

    def retrieve_discharges_of_intakes():
        """Return the dict of intake to its discharge time series."""
        pass

    def retrieve_discharges_of_pumps(self):
        """Return the dict of pump to its discharge time series."""
        pass

    def retrieve_sewer(self):
        """Return the time series of the sewer."""
        pass

    def get_max_intake(self):
        """Return the total capacity in [m3/day] of all the intakes combined.

        """
        pass

    def get_max_outlet(self):
        """Return the total capacity in [m3/day] of all the pumps combined.
        """
        pass


    def retrieve_pumping_stations_for_level_control(self):
        """Return the pair (intakes, pumps) pumping stations for level control.

        If the user did not define an intake for level control, this funtion
        returns None for that intake. The same holds for the pump for level
        control.

        """
        pass
