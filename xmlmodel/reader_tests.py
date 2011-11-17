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

from reader import parse_parameters
from reader import attach_timeseries_to_structures
from timeseries.timeseries import TimeSeries
import logging
from nens import mock
import unittest

from datetime import datetime


class CoupleParametersWithTimeseriesTest(unittest.TestCase):
    def setUp(self):
        self.root = parse_parameters("xmlmodel/gebiedsbeschrijving.xml")
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
        attach_timeseries_to_structures(self.root, tsd, k)

    def test_select_timeseries_precipitation(self):
        start = datetime(1991, 01, 02)
        end = datetime(1991, 01, 04)
        self.assertEquals(1, self.root.bucket[0].precipitation[start][0])
        self.assertEquals(3, self.root.bucket[0].precipitation[end][0])

    def test_retrieve_from_timeseries_precipitation(self):
        start = datetime(1991, 01, 02)
        end = datetime(1991, 01, 04)
        current = self.root.bucket[0].retrieve_precipitation(start, end)
        self.assertEquals(3, len(current))
        current = dict(current)
        self.assertEquals(1, current[start][0])
        self.assertEquals(3, current[end][0])

    def test_select_timeseries_evaporation(self):
        start = datetime(1991, 01, 02)
        end = datetime(1991, 01, 04)
        self.assertEquals(3, self.root.bucket[0].evaporation[start][0])
        self.assertEquals(7, self.root.bucket[0].evaporation[end][0])

    def test_retrieve_from_timeseries_evaporation(self):
        start = datetime(1991, 01, 02)
        end = datetime(1991, 01, 04)
        current = self.root.bucket[0].retrieve_evaporation(start, end)
        self.assertEquals(3, len(current))
        current = dict(current)
        print current
        self.assertEquals(3, current[start][0])
        self.assertEquals(7, current[end][0])

    def test_retrieve_not_existing_gives_exception(self):
        with self.assertRaises(AttributeError) as cm:
            self.root.bucket[0].retrieve_something_else()

        the_exception = cm.exception
        self.assertTrue(the_exception.message.endswith(
                "has no attribute 'retrieve_something_else'"))


class CouplingLogsMismatchesTest(unittest.TestCase):
    def setUp(self):
        self.handler = mock.Handler()
        logging.getLogger().addHandler(self.handler)
        self.root = parse_parameters("xmlmodel/gebiedsbeschrijving.xml")
        self.tsd = TimeSeries.as_dict("xmlmodel/first_small.xml")

    def tearDown(self):
        logging.getLogger().removeHandler(self.handler)

    def test_validate_reports_missing_properties(self):
        self.handler.flush()
        self.assertEquals(False, self.root.validate())
        self.assertEquals([], self.handler.content)
        
    
    def test_unused_series_logged_at_info(self):
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        'seepage': 'KWEL',
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                'seepage': 'KWEL',
                                },
             }
        
        attach_timeseries_to_structures(self.root, self.tsd, k)
        ## self.assertEquals([], handler.content)
        ## TODO - work in progress - issue #24
