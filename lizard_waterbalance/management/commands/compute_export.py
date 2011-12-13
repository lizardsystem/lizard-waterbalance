#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Implements a management command to compute and export a waterbalance."""

# This package implements the management commands for lizard-waterbalance Django
# app.
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

from datetime import datetime

from django.core.cache import cache
from django.core.management.base import BaseCommand

from dbmodel.models import Area
from dbmodel.models import PumpingStation
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.views import CacheKeyName
from lizard_waterbalance.views import CachedWaterbalanceComputer
from timeseries.timeseriesstub import write_to_pi_file

def replace_pumping_station_keys(mapping2series, name):
    pumping_stations2series = [name]
    del mapping2series[name]
    for pumping_station, series in pumping_stations2series.iteritems():
            mapping2series[pumping_station.name] = series

class Command(BaseCommand):
    """Implements a management command to compute and export a waterbalance.

    The client has to pass a WaterbalanceArea slug and a WaterbalanceScenario
    slug to the management command. The command uses these slugs to uniquely
    identify the WaterbalanceConf for which it has to compute and export the
    waterbalance.

    """
    args = "area-slug scenario-slug ['export-impact-all'|'export-impact-open-water']"
    help = "Computes the waterbalance of the given configuration and exports " \
           "the resulting time series to PI XML files in the current " \
           "directory."

    def __init__(self, *args, **kwargs):
        """Call __init__ of the parent class and pass the given parameters."""
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        """Parse the parameters and delegate the work specified by them."""
        if len(args) >= 2:
            area_slug, scenario_slug = tuple(args[0:2])
            if len(args) == 3:
                export_impact = args[2]
            else:
                export_impact = None
            configurations = WaterbalanceConf.objects
            configuration = configurations.get(waterbalance_area__slug=area_slug,
                                               waterbalance_scenario__slug=scenario_slug)
            computer = self.create_computer(configuration)
            if export_impact is None:
                self.compute_export(computer)
            elif export_impact == 'export-impact-all':
                self.export_impact(computer)
            elif export_impact == 'export-impact-open-water':
                self.export_impact_open_water(computer)
            else:
                self.print_help("compute_export")
        else:
            self.print_help("compute_export")

    def create_computer(self, configuration):
        cache_key_name = CacheKeyName(configuration)
        names = [ "sluice_error", "total_outtakes", "incoming", "outgoing",
            "outcome", "pair", "ref_in", "ref_out", "sluice_error_waterlevel",
            "fractions_1", "fractions_2", "concentrations", "impact",
            "impact_incremental" ]
        key_names = [cache_key_name.get(name) for name in names]
        cache.delete_many(key_names)
        area = Area(configuration)
        return CachedWaterbalanceComputer(cache_key_name, configuration, area)

    def compute_export(self, computer):
        """Compute and export the waterbalance using the given computer."""

        start, end = datetime(2000, 1, 1), datetime(2000,12, 31)
        computer.compute(start, end)

        series = computer.calc_sluice_error_timeseries(start, end)
        write_to_pi_file(location_id = "SAP", parameter_id="sluice-error",
                         filename="sluice-error.xml", timeseries=series)

        incoming = computer.get_open_water_incoming_flows(start, end)
        incoming_pumping_stations = incoming['defined_input']
        del incoming['defined_input']
        for pumping_station, series in incoming_pumping_stations.iteritems():
            incoming[pumping_station.name] = series
        write_to_pi_file(location_id = "SAP",
                         filename="open-water-incoming-flows.xml", timeseries=incoming)

        outgoing = computer.get_open_water_outgoing_flows(start, end)
        outgoing_pumping_stations = outgoing['defined_output']
        del outgoing['defined_output']
        for pumping_station, series in outgoing_pumping_stations.iteritems():
            outgoing[pumping_station.name] = series
        write_to_pi_file(location_id = "SAP",
                         filename="open-water-outgoing-flows.xml", timeseries=outgoing)

        level_control = computer.get_level_control_timeseries(start, end)
        write_to_pi_file(location_id = "SAP",
                         filename="level-control-timeseries.xml", timeseries=level_control)

        reference = {}
        intakes, outtakes = computer.get_reference_timeseries(start, end)
        for pumping_station, series in intakes.iteritems():
            reference[pumping_station.name] = series
        for pumping_station, series in outtakes.iteritems():
            reference[pumping_station.name] = series
        write_to_pi_file(location_id = "SAP",
                         filename="reference.xml", timeseries=reference)

        pair = computer.get_waterlevel_with_sluice_error(start, end)
        series = { "water_level": pair[0], "sluice_error": pair[1] }
        write_to_pi_file(location_id = "SAP",
                         filename="water-level-sluice-error.xml", timeseries=series)

        fractions = computer.get_fraction_timeseries(start, end)
        fractions_pumping_stations = fractions['intakes']
        del fractions['intakes']
        for pumping_station, series in fractions_pumping_stations.iteritems():
            fractions[pumping_station.name] = series
        write_to_pi_file(location_id = "SAP",
                         filename="fractions.xml", timeseries=fractions)

        series, delta = computer.get_concentration_timeseries(start, end)
        write_to_pi_file(location_id = "SAP", parameter_id = "concentration",
                         filename="concentration.xml", timeseries=series)

    def export_impact(self, computer):
        start, end = datetime(2000, 1, 1), datetime(2000,12, 31)
        computer.compute(start, end)

        impact = {}
        loads, loads_incremental = computer.get_impact_timeseries(start, end)
        for load in loads:
            impact[load.name] = load.timeseries
        write_to_pi_file(location_id = "SAP",
                         filename="impact.xml", timeseries=impact)
        for load in loads_incremental:
            impact[load.name] = load.timeseries
        write_to_pi_file(location_id = "SAP",
                         filename="impact-incremental.xml", timeseries=impact)

    def export_impact_open_water(self, computer):
        start, end = datetime(2000, 1, 1), datetime(2000,12, 31)
        computer.compute(start, end)

        impact = {}
        loads, loads_incremental = computer.get_impact_timeseries(start, end)
        for load in loads:
            if load.on_open_water_flow():
                impact[load.name] = load.timeseries
        write_to_pi_file(location_id = "SAP",
                         filename="impact-open-water.xml", timeseries=impact)
        for load in loads_incremental:
            if load.on_open_water_flow():
                impact[load.name] = load.timeseries
        write_to_pi_file(location_id = "SAP",
                         filename="impact-incremental-open-water.xml", timeseries=impact)
