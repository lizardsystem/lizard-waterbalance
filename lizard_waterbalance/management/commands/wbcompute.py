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
# Copyright 2011 Nelen & Schuurmans
#
#******************************************************************************
#
# initial programmer: Mario Frasca
# initial version:    2011-11-08
#
#******************************************************************************

import logging
from xml.dom.minidom import parse
from xmlmodel.reader import parse_parameters
from xmlmodel.reader import attach_timeseries_to_structures

from django.core.management.base import BaseCommand

from timeseries.timeseries import TimeSeries

log = logging.getLogger(__name__)

def getText(node):
    return str("".join(t.nodeValue for t in node.childNodes
                       if t.nodeType == t.TEXT_NODE))


ASSOC = {'Bucket': {'precipitation': 'NEERSG',
                    'evaporation': 'VERDPG',
                    'seepage': 'KWEL',
                    'infiltration': 'WEGZ',
                    'water_level': 'WATHTE',
                    'sewer': '',
                    'minimum_level': 'MARG_OND',
                    'maximum_level': 'MARG_BOV',
                    'nutricalc_min': '',
                    'nutricalc_incr': '',
                    },
         'PumpingStation': {'precipitation': 'NEERSG',
                            'evaporation': 'VERDPG',
                            'seepage': 'KWEL',
                            'infiltration': 'WEGZ',
                            'water_level': 'WATHTE',
                            'sewer': '',
                            'minimum_level': 'MARG_OND',
                            'maximum_level': 'MARG_BOV',
                            'nutricalc_min': '',
                            'nutricalc_incr': '',
                            },
         }





class Command(BaseCommand):
    args = "<run file>"
    help = "to be used as a general adapter"

    def handle(self, *args, **options):
        run_file = str(args[0])
        run_dom = parse(run_file)
        root = run_dom.childNodes[0]
        run_info = dict([(i.tagName, getText(i))
                         for i in root.childNodes
                         if i.nodeType != i.TEXT_NODE
                         and i.tagName != u"properties"])
        diag = open(run_info['outputDiagnosticFile'], "w")
        diag.write("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Diag version="1.2" xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI HTTP://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_diag.xsd"/>
""")
        diag.close()
        log.debug(run_info['inputTimeSeriesFile'])
        tsd = TimeSeries.as_dict(run_info['inputTimeSeriesFile'])
        area = parse_parameters(run_info['inputParameterFile'])
        attach_timeseries_to_structures(area, tsd, ASSOC)

        result = tsd
        TimeSeries.write_to_pi_file(run_info['outputTimeSeriesFile'], result)
