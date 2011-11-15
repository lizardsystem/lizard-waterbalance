#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=C0111

# The lizard_wbcomputation package implements the functionality to compute a
# waterbalance.
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

class BucketTypes(object):
    """Identifies the differen bucket types.

    'Bucket' is the english term for 'bakje'.

    """
    UNDRAINED_SURFACE = 0
    HARDENED_SURFACE = 1
    DRAINED_SURFACE = 2
    STEDELIJK_SURFACE = 3
    SURFACE_TYPES = (
        (UNDRAINED_SURFACE, "ongedraineerd"),
        (HARDENED_SURFACE, "verhard"),
        (DRAINED_SURFACE, "gedraineerd"),
        (STEDELIJK_SURFACE, "stedelijk"))

