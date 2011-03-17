#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Bastiaan Roos
#
#******************************************************************************

from datetime import datetime
from os.path import join
    
from django.core.management.base import BaseCommand

from lizard_waterbalance.models import WaterbalanceArea
            

class Command(BaseCommand):
    args = "<filelocation namefield epsg_of_shapefile>"
    help = "Load shapefile with geometries and names into WaterbalanceArea table."

    def handle(self, *args, **options):
        method = 1 #hardcoded, option or remove other method?
        directory = args[0]
        shapefile_name = str(args[1])
        name_field = str(args[2])
        source_epsg = int(args[3])

        WaterbalanceArea._load_shapefile(self, shapefile_name, name_field, source_epsg)






