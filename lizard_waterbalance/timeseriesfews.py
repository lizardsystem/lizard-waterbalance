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

from django.db import models
from django.utils.translation import ugettext as _

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeseriedata


class TimeseriesFews(models.model):
    """Specifies a time series in a Fews unblobbed database.

    A time series is a sequence of events, where an event is a value - date
    time pair.

    """

    fews_location = models.ForeignKey(Location, verbose_name=_("locatie"),
                                      help_text=_("locatie in FEWS unblobbed"),
                                      null=True, blank=True, related_name='+')

    fews_filter = models.ForeigKey(Filter, verbose_name=_("filter"),
                                   help_text=_("filter in FEWS unblobbed"),
                                   null=True, blank=True, related_name='+')

    fews_parameter = models.ForeignKey(Parameter, verbose_name=_("parameter"),
                                       help_text=_("parameter in FEWS unblobbed"),
                                       null=True, blank=True, related_name='+')

    fews_timeseries = models.ForeignKey(Timeseriedata, related_name='+')

    def events(self):
        """Return a generator to iterate over all events.

        The generator iterates over the events earliest date first.

        """
        for event in self.fews_timeseries.timeserie_data.all.objects.order_by('tsd_time'):
            yield event.tsd_time, event.tsd_value
