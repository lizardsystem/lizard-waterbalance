#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The dbmodel package provides an interface to the data required by the
# computational core of the lizard waterbalance Django app. This data is stored
# in multiple databases.
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

import logging

from lizard_waterbalance.models import IncompleteData
from lizard_waterbalance.models import PumpingStation as DatabasePumpingStation
from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import map_timeseries
from timeseries.timeseriesstub import SparseTimeseriesStub
from timeseries.timeseriesstub import TimeseriesRestrictedStub
from timeseries.timeseriesstub import TimeseriesWithMemoryStub

logger = logging.getLogger(__name__)

class Area(object):

    def __init__(self, configuration):

        self.configuration = configuration

    @property
    def surface(self):
        """Return the surface of the current Area in [m2]."""
        return self.configuration.open_water.surface

    @property
    def bottom_height(self):
        """Return the bottom height of the current Area in [mNAP]."""
        return self.configuration.open_water.bottom_height

    @property
    def init_water_level(self):
        """Return the initial water level of the current Area in [mNAP]."""
        return self.configuration.open_water.init_water_level

    @property
    def max_intake(self):
        """Return the max capacity of an intake of the current Area in [mNAP].

        The intake should be an intake for level control.

        """
        max_discharge = 0.0
        is_none = True
        for station in self.pumping_stations:
            if station.into and station.computed_level_control:
                if station.max_discharge is not None:
                    max_discharge += station.max_discharge
                    is_none = False

        if is_none:
            return None
        else:
            return max_discharge

    @property
    def max_outtake(self):
        """Return the max capacity of a pump of the current Area in [mNAP].

        The intake should be a pump for level control.

        """
        max_discharge = 0.0
        is_none = True
        for station in self.pumping_stations:
            if (not station.into) and station.computed_level_control:
                if station.max_discharge is not None:
                    max_discharge += station.max_discharge
                    is_none = False

        if is_none:
            return None
        else:
            return max_discharge

    @property
    def buckets(self):
        """Return the Bucket(s) for the current Area."""
        config = self.configuration
        database_buckets = config.open_water.buckets.all()
        new_buckets = [Bucket(config, b) for b in database_buckets]
        return map(lambda b:b.store_new_properties(), new_buckets)

    @property
    def pumping_stations(self):
        """Return the PumpingStation(s) for the current Area."""
        open_water = self.configuration.open_water
        stations = []
        for s in DatabasePumpingStation.objects.filter(open_water=open_water):
            station = PumpingStation(self.configuration, s)
            station.copy_properties()
            stations.append(station)
        return stations

    def retrieve_precipitation(self, start_date, end_date):
        """Return the precipitation time series for the current Area.

        In case no precipitation time series is defined, this method throws an
        IncompleteData exception.

        """
        open_water = self.configuration.open_water
        if open_water.precipitation is None:
            exception_msg = "No precipitation is defined for the " \
                "waterbalance area %s" % unicode(open_water)
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = open_water.precipitation.get_timeseries()
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_evaporation(self, start_date, end_date):
        """Return the evaporation time series for the current Area.

        In case no evaporation time series is defined, this method throws an
        IncompleteData exception.

        """
        open_water = self.configuration.open_water
        if open_water.evaporation is None:
            exception_msg = "No evaporation is defined for the waterbalance " \
                "area %s" % unicode(open_water)
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = open_water.evaporation.get_timeseries()
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_seepage(self, start_date, end_date):
        """Return the seepage time series for the current Area.

        In case no seepage time series is defined, this method throws an
        IncompleteData exception.

        """
        open_water = self.configuration.open_water
        if open_water.seepage is None:
            exception_msg = "No seepage is defined for the waterbalance " \
                            "area %s" %  unicode(open_water)
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = open_water.seepage.get_timeseries()
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_sewer(self, start_date, end_date):
        """Return the sewer time series for the current Area.

        It is possible no sewer time series has been defined. In that case,
        this method will return None.

        """
        open_water = self.configuration.open_water
        if open_water.sewer is None:
            return None

        timeseries = open_water.sewer.get_timeseries()
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_minimum_level(self, start_date, end_date):
        """Return the minimum water level for the current Area."""
        open_water = self.configuration.open_water
        if open_water.use_min_max_level_relative_to_meas:
             min_level = TimeseriesWithMemoryStub()
             min_level.add_value(start_date, open_water.min_level_relative_to_measurement)
             return add_timeseries(min_level, open_water.waterlevel_measurement.get_timeseries())
        else:
            return TimeseriesRestrictedStub(timeseries=open_water.minimum_level.get_timeseries(),
                                            start_date=start_date,
                                            end_date=end_date)

    def retrieve_maximum_level(self, start_date, end_date):
        """Return the maximum water level for the current Area."""
        open_water = self.configuration.open_water
        if open_water.use_min_max_level_relative_to_meas:
             max_level = TimeseriesWithMemoryStub()
             max_level.add_value(start_date, open_water.max_level_relative_to_measurement)
             return add_timeseries(max_level, open_water.waterlevel_measurement.get_timeseries())
        else:
            return TimeseriesRestrictedStub(timeseries=open_water.maximum_level.get_timeseries(),
                                        start_date=start_date,
                                        end_date=end_date)


    def retrieve_nutricalc_min(self, start_date, end_date):
        """Return the minimal nutricalc time series for the current Area.

        If no such time series is defined, this method returns None.

        """
        open_water = self.configuration.open_water
        if open_water.nutricalc_min is not None:
            timeseries = open_water.nutricalc_min.get_timeseries()
            return TimeseriesRestrictedStub(timeseries=timeseries,
                                            start_date=start_date,
                                            end_date=end_date)
        else:
            return None

    def retrieve_nutricalc_incr(self, start_date, end_date):
        """Return the incremental nutricalc time series for the current Area.

        If no such time series is defined, this method returns None.

        """
        open_water = self.configuration.open_water
        if open_water.nutricalc_incr is not None:
            timeseries = open_water.nutricalc_incr.get_timeseries()
            return TimeseriesRestrictedStub(timeseries=timeseries,
                                            start_date=start_date,
                                            end_date=end_date)
        else:
            return None


    @property
    def concentr_chloride_precipitation(self):
        """Return the chloride concentration of the precipitation.

        This value is None when no Label exists with the program name
        'precipitation'.

        """
        for concentr in self.configuration.config_concentrations.all().select_related('Label'):
            if concentr.label.program_name == "precipitation":
                return concentr.cl_concentration
        return None

    @property
    def concentr_chloride_seepage(self):
        """Return the chloride concentration of the seepage.

        This value is None when no Label exists with the program name
        'seepage'.

        """
        for concentr in self.configuration.config_concentrations.all().select_related('Label'):
            if concentr.label.program_name == "seepage":
                return concentr.cl_concentration

    @property
    def min_concentr_phosphate_precipitation(self):
        pass

    @property
    def incr_concentr_phosphate_precipitation(self):
        pass

    @property
    def min_concentr_phosphate_seepage(self):
        pass

    @property
    def incr_concentr_phosphate_seepage(self):
        pass

    @property
    def min_concentr_nitrogyn_precipitation(self):
        pass

    @property
    def incr_concentr_nitrogyn_precipitation(self):
        pass

    @property
    def min_concentr_nitrogyn_seepage(self):
        pass

    @property
    def incr_concentr_nitrogyn_seepage(self):
        pass


class Bucket(object):

    def __init__(self, configuration, database_bucket):
        self.configuration = configuration
        self.database_bucket = database_bucket

    def store_new_properties(self):
        """Store the properties that do not belong to the database bucket."""
        self.name = self.database_bucket.name
        self.surface_type = self.database_bucket.surface_type
        self.surface = self.database_bucket.surface
        self.bottom_porosity = self.database_bucket.porosity
        self.crop_evaporation_factor = self.database_bucket.crop_evaporation_factor
        self.min_crop_evaporation_factor = self.database_bucket.min_crop_evaporation_factor
        self.bottom_drainage_fraction = self.database_bucket.drainage_fraction
        self.bottom_indraft_fraction = self.database_bucket.indraft_fraction
        self.bottom_max_water_level = self.database_bucket.max_water_level
        self.bottom_min_water_level = self.database_bucket.min_water_level
        self.bottom_equi_water_level = self.database_bucket.equi_water_level
        self.bottom_init_water_level = self.database_bucket.init_water_level
        self.external_discharge = self.database_bucket.external_discharge
        self.porosity = self.database_bucket.upper_porosity
        self.drainage_fraction = self.database_bucket.upper_drainage_fraction
        self.indraft_fraction = self.database_bucket.upper_indraft_fraction
        self.max_water_level = self.database_bucket.upper_max_water_level
        self.min_water_level = self.database_bucket.upper_min_water_level
        self.equi_water_level = self.database_bucket.upper_equi_water_level
        self.init_water_level = self.database_bucket.upper_init_water_level
        # self.concentr_chloride_flow_off = self._get_concentr_chloride_flow_off()
        # self.label_flow_off = self._get_label_flow_off()
        return self

    def retrieve_seepage(self, start_date, end_date):
        """Return the seepage time series for the current Bucket.

        In case no seepage time series is defined, this method throws an
        IncompleteData exception.

        """
        if self.database_bucket.seepage is None:
            exception_msg = "No seepage is defined for bucket %s" % \
                            unicode(self.database_bucket)
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.database_bucket.seepage.get_timeseries()
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def _get_concentr_chloride_flow_off(self):
        """Return the chloride concentration of the flow off.

        This value is None when no Label exists with a program name equal to
        the program name of the label of the bucket.

        """
        for concentr in self.configuration.config_concentrations.all().select_related('Label'):
            if concentr.label.program_name == self.database_bucket.label.program_name:
                return concentr.cl_concentration

    def _get_label_flow_off(self):
        """Return the label of the bucket."""
        return self.database_bucket.label.program_name


class PumpingStation(object):

    def __init__(self, configuration, db_station):
        self.configuration = configuration
        self.db_station = db_station

    def copy_properties(self):
        """Store the properties that do not belong to the database bucket."""
        self.concentr_chloride_flow_off = self._get_concentr_chloride_flow_off()
        self.label_flow_off = self._get_label_flow_off()
        self.into = self.db_station.into
        self.computed_level_control = self.db_station.computed_level_control
        self.max_discharge = self.db_station.max_discharge
        self.label = self.db_station.label
        self.name = self.db_station.name
        return self

    def retrieve_sum_timeseries(self):
        """Return the sum of the time series of each of its PumpLine(s).

        If the current PumpingStation is an intake, this method returns a time
        series whose values are non-negative and if it is a pump, this method
        returns a time series whose values are non-positive. This holds even
        if the stored event values have a different sign.

        """
        result = SparseTimeseriesStub()
        factor = (1.0 if self.into else -1.0)
        map_f = lambda v: factor * abs(v)
        for pump_line in self.db_station.pump_lines.all():
            timeseries = map_timeseries(pump_line.retrieve_timeseries(), map_f)
            result = add_timeseries(result, timeseries)
        return result

    def _get_concentr_chloride_flow_off(self):
        """Return the chloride concentration of the flow off.

        This value is None when no Label exists with a program name equal to
        the program name of the label of the bucket.

        """
        for concentr in self.configuration.config_concentrations.all().select_related('Label'):
            if concentr.label.program_name == self.db_station.label.program_name:
                return concentr.cl_concentration

    def _get_label_flow_off(self):
        """Return the label of the bucket."""
        return self.db_station.label.program_name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        """Return True iff self is semantically equal to other."""
        is_equal = False
        try:
            is_equal = self.name == other.name
        except AttributeError:
            pass
        return is_equal
