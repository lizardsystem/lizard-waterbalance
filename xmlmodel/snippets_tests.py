#!/usr/bin/python
# -*- coding: utf-8 -*-
#***********************************************************************
#
# This file is part of the waterbalance program.
#
# the waterbalance program is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# the waterbalance program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the nens libraray.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Copyright 2011 Nelen & Schuurmans
#*
#***********************************************************************
#*
#* $Id: turtleurbanclasses_tests.py 24585 2011-10-03 12:35:00Z mario.frasca $
#*
#* initial programmer :  Mario Frasca
#* initial date       :  2011-11-07
#**********************************************************************

from snippets import parse_parameters
from snippets import attach_timeseries_to_structures
from timeseries.timeseries import TimeSeries

import unittest

from datetime import datetime

class ObjectCreateTest(unittest.TestCase):
    def test0Pass(self):
        root = parse_parameters("xmlmodel/gebiedsbeschrijving.xml")
        tsd = TimeSeries.as_dict("xmlmodel/first_small.xml")
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        'seepage': 'KWEL',
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                'seepage': 'KWEL',
                                },
             }
        attach_timeseries_to_structures(root, tsd, k)
        start = datetime(1991, 01, 02)
        end = datetime(1991, 01, 04)
        current = root.bucket[0].retrieve_precipitation(start, end)
        self.assertEquals(3, len(current))
        current = dict(current)
        self.assertEquals(3, current[start])
        self.assertEquals(7, current[end])
