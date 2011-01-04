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
# Initial programmer: Pieter Swinkels
#
#******************************************************************************

import sys

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import PumpingStation

def retrieve_definitions(filename):
    """Return the list of records stored in the file with the given name.

    Each element of th list that this function returns is a dictionary of field
    name to field value (as a string).

    Each line of the file with the given name specifies a record, where each
    field is separated from the next through a comma. The first line of the
    file specifies the name of each field.

    """
    definitions = []
    f = open(filename)
    first_line = True
    for line in f.readlines():
        if first_line:
            labels = [label.rstrip("\r\n") for label in line.split(',')]
            first_line = False
        else:
            values = [value.rstrip("\r\n") for value in line.split(',')]
            definitions.append(dict(zip(labels, values)))
    f.close()
    return definitions

def import_pumpingstations(filename):

    for pumpingstation_definition in retrieve_definitions(filename):
        print pumpingstation_definition
        pumpingstation = PumpingStation()

        pumpingstation.name = pumpingstation_definition['name']
        pumpingstation.into = pumpingstation_definition['into'].lower() == "true"
        pumpingstation.percentage = int(pumpingstation_definition['percentage'])
        pumpingstation.save()

def import_openwaters(filename):

    for openwater_definition in retrieve_definitions(filename):
        print openwater_definition
        openwater = OpenWater()

        openwater.name = openwater_definition['name']
        openwater.slug = "Aetseveldsepolder oost - %s" % openwater.name

        openwater.surface = int(float(openwater_definition['surface']))
        openwater.save()

def import_buckets(filename):
    bucket_definitions = []

    f = open(filename)
    first_line = True
    for line in f.readlines():
        if first_line:
            labels = [label.rstrip("\r\n") for label in line.split(',')]
            first_line = False
        else:
            values = [value.rstrip("\r\n") for value in line.split(',')]
            bucket_definitions.append(dict(zip(labels, values)))

    for bucket_definition in bucket_definitions:
        print bucket_definition
        bucket = Bucket()
        # we do not use bucket_definition['uitspoel']
        # we do not use bucket_definition['code']
        # we do not use bucket_definition['indraft']
        bucket.surface = int(float(bucket_definition['surface']))
        # we do not use bucket_definition['ol minimum level']
        # we do not use bucket_definition['flow_off']
        # we do not use bucket_definition['infiltration']
        bucket.min_crop_evaporation_factor = float(bucket_definition['bl min. Gewasverdampingsfactor (-)'])
        bucket.init_water_level = float(bucket_definition['bl init level'])
        bucket.max_water_level = float(bucket_definition['bl max level'])
        # we do not use bucket_definition['ol max level']
        bucket.min_water_level = float(bucket_definition['bl minimum level'])
        # we do not use bucket_definition['open_water']
        # we do not use bucket_definition['ol init level']
        # we do not use bucket_definition['ol equilibrium level']
        bucket.equi_water_level = bucket_definition['bl equilibrium level']
        # we do not use bucket_definition['ol f_intrek']
        # we do not use bucket_definition['ol_volume']
        bucket.porosity = float(bucket_definition['bl porositeit / bergingsruimte'])
        # we do not use bucket_definition['nr']
        bucket.crop_evaporation_factor = bucket_definition['bl gewasverdampingsfactor (-)']

        bucket.name = bucket_definition['name']
        if bucket.name == "verhard":
            bucket.type = Bucket.HARDENED_SURFACE
        elif bucket.name[0:len("gedraineerd")] == "gedraineerd":
            bucket.type = Bucket.DRAINED_SURFACE
        else:
            bucket.type = Bucket.UNDRAINED_SURFACE
        bucket.slug = "Aetseveldsepolder oost - %s" % bucket.name

        if bucket.type != Bucket.DRAINED_SURFACE:
            bucket.upper_porosity = 1.0
        else:
            bucket.upper_porosity = float(bucket_definition['ol porositeit / bergingsruimte'])

        if bucket.type != Bucket.UNDRAINED_SURFACE:
            bucket.upper_crop_evaporation_factor = float(bucket_definition['ol gewasverdampingsfactor (-)'])
            bucket.upper_min_crop_evaporation_factor = float(bucket_definition['ol min. Gewasverdampingsfactor (-)'])
        else:
            bucket.upper_crop_evaporation_factor = 1.0
            bucket.upper_min_crop_evaporation_factor = 1.0
            bucket.upper_porosity = 1.0

        # we do not use bucket_definition['bl_volume']
        # we do not use bucket_definition['computed_flow_off']
        # we do not use bucket_definition['ol f_uitpoel']
        bucket.drainage_fraction = float(bucket_definition['bl f_uitpoel'])
        # we do not use bucket_definition['seepage']
        bucket.indraft_fraction = float(bucket_definition['bl f_intrek'])
        bucket.save()

if __name__ == "__main__":

    if len(sys.argv) == 2:
        import_buckets(sys.argv[1])

