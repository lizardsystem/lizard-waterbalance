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

from django.core.management.base import BaseCommand

from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.views import CacheKeyName
from lizard_waterbalance.views import CachedWaterbalanceComputer

from timeseries.timeseriesstub import write_to_pi_file


class Waterbalance(object):
    """Implements the functionality to compute and export a waterbalance."""

    def compute_export(self, area_slug, scenario_slug):
        """Compute and export the waterbalance for the given configuration."""
        configurations = WaterbalanceConf.objects
        configuration = configurations.get(waterbalance_area__slug=area_slug,
             waterbalance_scenario__slug=scenario_slug)

        cache_key_name = CacheKeyName(configuration)
        computer = CachedWaterbalanceComputer(cache_key_name, configuration)
        start, end = datetime(2000, 1, 1), datetime(2000,12, 31)
        computer.compute(start, end)

        series =  computer.calc_sluice_error_timeseries(start, end)
        write_to_pi_file(location_id = "SAP", parameter_id="sluice-error",
                         filename="sluice-error.xml", timeseries=series)


class Command(BaseCommand):
    """Implements a management command to compute and export a waterbalance.

    The client has to pass a WaterbalanceArea slug and a WaterbalanceScenario
    slug to the management command. The command uses these slugs to uniquely
    identify the WaterbalanceConf for which it has to compute and export the
    waterbalance.

    """
    args = "area-slug scenario-slug"
    help = "Computes the waterbalance of the given configuration and exports " \
           "the resulting time series to PI XML files in the current " \
           "directory."

    def __init__(self, *args, **kwargs):
        """Call __init__ of the parent class and pass the given parameters."""
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):
        """Parse the parameters and delegate the work specified by them."""
        if len(args) == 2:
            area_slug, scenario_slug = tuple(args)
            Waterbalance().compute_export(area_slug, scenario_slug)
        else:
            self.print_help("compute_export")
