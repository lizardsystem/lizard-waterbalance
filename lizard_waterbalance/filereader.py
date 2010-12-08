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
# Initial date:       2010-12-07
#
#******************************************************************************


class FileReader:

    def open(self, filename):
        self.file = open(filename)

    def readlines(self):
        return self.file.readlines()

    def close(self):
        self.file.close()

class FileReaderStub():

    def __init__(self, lines):
        self.lines = lines

    def open(self, filename):
        return self.lines

    def readlines(self):
        return self.lines

    def close(self):
        pass
