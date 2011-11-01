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

from lizard_waterbalance.models import PumpingStation

class Area(object):

    def __init__(self, configuration):

        self.configuration = configuration

    @property
    def surface(self):
        """Return the surface of the current Area in [m2]."""
        return self.configuration.open_water.surface

    @property
    def buckets(self):
        """Return the Bucket(s) for the current Area."""
        return self.configuration.open_water.buckets.all()

    @property
    def pumping_stations(self):
        """Return the PumpingStation(s) for the current Area."""
        open_water = self.configuration.open_water
        return PumpingStation.objects.filter(open_water=open_water)

