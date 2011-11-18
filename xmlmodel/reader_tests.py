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
import pkg_resources

from datetime import datetime


class CoupleParametersWithTimeseriesTest(unittest.TestCase):
    def setUp(self):
        self.testdata = pkg_resources.resource_filename(
            "xmlmodel", "testdata/")
        self.root = parse_parameters(self.testdata + "gebiedsbeschrijving.xml")
        tsd = TimeSeries.as_dict(self.testdata + "first_small.xml")
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

    def test_retrieve_functions_return_timeseries(self):
        start = datetime(1991, 01, 02)
        end = datetime(1991, 01, 04)
        current = self.root.bucket[0].retrieve_precipitation(start, end)
        self.assertEquals(TimeSeries, current.__class__)
        current = self.root.bucket[0].retrieve_precipitation(end=end)
        self.assertEquals(TimeSeries, current.__class__)
        current = self.root.bucket[0].retrieve_precipitation(start)
        self.assertEquals(TimeSeries, current.__class__)
        current = self.root.bucket[0].retrieve_precipitation()
        self.assertEquals(TimeSeries, current.__class__)

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
        self.assertEquals(3, len(list(current.events())))
        current = dict(current)
        print current
        self.assertEquals(3, current[start][0])
        self.assertEquals(7, current[end][0])

    def test_retrieve_not_existing_gives_exception(self):
        try:
            self.root.bucket[0].retrieve_something_else()
            self.fail("did not generate 'AttributeError' exception")
        except AttributeError as e:
            self.assertTrue(str(e).endswith(
                    "has no attribute 'retrieve_something_else'"))


class CouplingLogsMismatchesTest(unittest.TestCase):
    def setUp(self):
        self.handler = mock.Handler()
        logging.getLogger().addHandler(self.handler)
        self.testdata = pkg_resources.resource_filename(
            "xmlmodel", "testdata/")
        self.root = parse_parameters(self.testdata + "gebiedsbeschrijving.xml")
        self.tsd = TimeSeries.as_dict(self.testdata + "first_small.xml")

    def tearDown(self):
        logging.getLogger().removeHandler(self.handler)

    def test_validate_reports_missing_properties(self):
        self.handler.flush()
        self.assertEquals(False, self.root.validate())
        self.assertEquals(1, len(self.handler.content))
        self.assertTrue(self.handler.content[-1].endswith(
                'has no min_concentr_phosphate_seepage field'))

        self.handler.flush()
        self.root.min_concentr_phosphate_seepage = 0
        self.assertEquals(True, self.root.validate())
        self.assertEquals(0, len(self.handler.content))

    def test_not_found_series_logged_at_warning_01(self):
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        'seepage': 'KWEL',  # NOT IN DATA
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                'seepage': 'KWEL',  # NOT IN DATA
                                },
             }

        self.handler.setLevel(logging.WARNING)
        self.handler.flush()
        attach_timeseries_to_structures(self.root, self.tsd, k)
        self.assertEquals(10, len(self.handler.content))

    def test_not_found_series_logged_at_warning_02(self):
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                },
             }

        self.handler.setLevel(logging.WARNING)
        self.handler.flush()
        attach_timeseries_to_structures(self.root, self.tsd, k)
        self.assertEquals(4, len(self.handler.content))

    def test_not_found_series_logged_at_warning_03(self):
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                },
             }

        self.handler.setLevel(logging.WARNING)
        self.handler.flush()
        self.tsd['SAP_S2', 'NEERSG'] = self.tsd['SAP', 'NEERSG']
        self.tsd['SAP_S2', 'VERDPG'] = self.tsd['SAP', 'VERDPG']
        attach_timeseries_to_structures(self.root, self.tsd, k)
        self.assertEquals(0, len(self.handler.content))

    def test_unused_series_logged_at_info01(self):
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                },
             }
        self.handler.flush()
        attach_timeseries_to_structures(self.root, self.tsd, k)
        self.handler.content = [i for i in self.handler.content
                                if i.startswith("xmlmodel.reader|INFO|")]
        self.assertEquals(0, len(self.handler.content))

    def test_unused_series_logged_at_info02(self):
        k = {'Bucket': {'precipitation': 'NEERSG',
                        'evaporation': 'VERDPG',
                        'seepage': 'KWEL',  # NOT IN DATA
                        },
             'PumpingStation': {'precipitation': 'NEERSG',
                                'evaporation': 'VERDPG',
                                'seepage': 'KWEL',  # NOT IN DATA
                                },
             }

        self.handler.flush()
        attach_timeseries_to_structures(self.root, self.tsd, k)
        self.handler.content = [i for i in self.handler.content
                                if i.startswith("xmlmodel.reader|INFO|")]
        self.assertEquals(0, len(self.handler.content))

    def test_unused_series_all(self):
        k = {'Bucket': {},
             'PumpingStation': {},
             }

        self.handler.flush()
        attach_timeseries_to_structures(self.root, self.tsd, k)
        self.handler.content = [i for i in self.handler.content
                                if i.startswith("xmlmodel.reader|INFO|")]
        self.assertEquals(2, len(self.handler.content))
