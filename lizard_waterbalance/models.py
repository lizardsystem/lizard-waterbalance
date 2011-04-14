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

import logging
import datetime

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db import models
from django.db import transaction
from django.db.models import Max
from django.db.models import Min
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.db.models.signals import pre_save

from lizard_fewsunblobbed.models import Filter as FewsFilter
from lizard_fewsunblobbed.models import Location as FewsLocation
from lizard_fewsunblobbed.models import Parameter as FewsParameter
from lizard_fewsunblobbed.models import Timeserie as FewsTimeserie
from lizard_map.models import ColorField
from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import daily_events
from timeseries.timeseriesstub import daily_sticky_events
from timeseries.timeseriesstub import TimeseriesWithMemoryStub
from timeseries.timeseriesstub import TimeseriesRestrictedStub
from timeseries.timeseriesstub import SparseTimeseriesStub

# The following constant is defined because the length of the name of an
# OpenWater is used in two places, viz. in the definition of the name field and
# in the function pre_save_configuration
MAXLENGTH_OPENWATER_NAME = 64

logger = logging.getLogger(__name__)

def generate_events(events, default_value, sticky, start_date, end_date):
    """Return a generator to iterate over all the given events.

    If sticky holds, this method returns values for each day between the
    specified start and end, assuming start and end are not None. This means
    that for each day before the start for which no event exists, this method
    returns the default value. For each dat after the start for which no event
    exists, this method returns the value of the last event or if not present,
    the default value.

    """
    if sticky:
        if start_date is None or end_date is None:
            date_before_first_event = False
        else:
            date_before_first_event = True
            date = start_date
        value = default_value
        for event_date, event_value in daily_sticky_events(events):
            while date_before_first_event and date < event_date:
                yield date, default_value
                date = date + datetime.timedelta(1)
            yield event_date, event_value
            date_before_first_event = False
            date = event_date + datetime.timedelta(1)
            value = event_value
        while end_date is not None and date <= end_date:
            yield date, value
            date = date + datetime.timedelta(1)
    else:
        for date, value in daily_events(events, default_value=default_value):
            yield date, value


class IncompleteData(Exception):
    """Implements the exception when the model is not completely defined."""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Timeseries(models.Model):
    """Specifies a time series in the database of the current Django app.

    A time series is a sequence of events, where an event is a value - date
    time pair.

    To get to the events that belong to the current Timeseries, use the
    implicit attribute 'timeseries_events', which is a Manager for the events.

    """
    name = models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam om de tijdreeks eenvoudig te herkennen"),
        max_length=64, null=True, blank=True)

    default_value = models.FloatField(verbose_name=_("default value"),
                                      null=True, blank=True,
                                      default=0.0)

    stick_to_last_value = models.NullBooleanField(verbose_name=_("reeks met 'geheugen'"),
                                      null=True, blank=True,
                                      help_text=_("moet een waarde geldig blijven tot de eerst volgende waarde (blok functie)"),
                                      default=False)

    class Meta:
        verbose_name = _("7a Tijdreeks")
        verbose_name_plural = _("7a Tijdreeksen")

    def raw_events(self, start_date=None, end_date=None):
        """Return a generator to iterate over all events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function does
        not fill in the missing dates with value.

        """


        events = self.timeseries_events.filter().order_by('time')
        if start_date:
            events = events.filter(time__gte=start_date)
        if end_date:
            events = events.filter(time__lte=end_date)

        for event in events:
            yield event.time, event.value

    def get_last_event(self):
        """return event with latest datetime"""
        try:
            return self.timeseries_events.all().order_by('-time')[0]
        except:
            return None

    def waterbalance_timeserie_info(self):
        result = ""
        for link in self.wb_local.all():
            result += "waterbalance timeserie '%s' (%i)"%(link.__unicode__(), link.id)
        return result


    def events(self, start_date=None, end_date=None):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates. Which value is inserted depends on the values of
        self.stick_to_last_value and self.default, for details also see the doc
        string of functions timeseries.daily_events and
        timeseries.daily_sticky_events.

        If self.stick_to_last_value holds, this method returns values for each
        day between the specified start and end, assuming start and end are not
        None. This means that for each day before the start or after the and
        for which no event exists, this method returns the default value.

        .. todo::

           Method Timeseries.events returns the dates including the end date, whereas
           on other locations in the code the end date is not included. The same holds
           for method TimeseriesFews.events.

        """
        ts_events = self.timeseries_events.filter().order_by('time')
        if not start_date is None:
            ts_events = ts_events.filter(time__gte=start_date)
        if not end_date is None:
            ts_events = ts_events.filter(time__lte=end_date)

        events = ((event.time, event.value) for event in ts_events)
        for date, value in generate_events(events, self.default_value,
                                           self.stick_to_last_value,
                                           start_date, end_date):
            yield date, value

    @transaction.commit_manually
    def save_timeserie_stub(self,timeserie_stub):
        """Save a timeserie_stub into the database

        We need some performance boost on this function
        #first clear?
        """
        for date, value in timeserie_stub.raw_events():
            ts = TimeseriesEvent(time=date, value=value, timeseries=self)
            ts.save()

        transaction.commit()

    def times_values(self, start_date, end_date):
        """
        Produce times and values list, use for matplotlib.
        """
        times = []
        values = []
        for event in self.timeseries_events.filter(
            time__gte=start_date,
            time__lte=end_date):

            times.append(event.time)
            values.append(event.value)
        return times, values


    def __unicode__(self):
        return self.name


class TimeseriesEvent(models.Model):
    """Specifies a single event, that is, a value - date time pair.

    Instance variables:
    * value -- value of the event
    * time -- date time of the event
    * timeseries -- link to the time serie

    """
    class Meta:
        verbose_name = _("Tijdreeks event")
        verbose_name_plural = _("Tijdreeks events")
        ordering = ["time"]

    time = models.DateTimeField()
    value = models.FloatField()

    timeseries = models.ForeignKey(Timeseries, related_name='timeseries_events')

    def __unicode__(self):
        return u'Event %s: (%s, %s)' % (self.timeseries, self.time, self.value)


class TimeseriesFews(models.Model):
    """Specifies a time series in a Fews unblobbed database.

    A time series is a sequence of events, where an event is a value - date
    time pair.

    """
    class Meta:
        verbose_name = _("7b tijdreeks FEWS")
        verbose_name_plural = _("7b tijdreeksen FEWS")

    name = models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam om de tijdreeks eenvoudig te herkennen"),
        max_length=64, null=True, blank=True)


    default_value = models.FloatField(verbose_name=_("default value"),
                                      null=True, blank=True,
                                      default=0.0)

    stick_to_last_value = models.NullBooleanField(verbose_name=_("reeks met 'geheugen'"),
                                      null=True, blank=True,
                                      help_text=_("moet een waarde geldig blijven tot de eerst volgende waarde (blok functie)"),
                                      default=False)

    pkey = models.IntegerField(
        verbose_name=_("Parameter"),
        help_text=_("pkey van de parameter in FEWS unblobbed"),
        null=True, blank=True)

    fkey = models.IntegerField(
        verbose_name=_("Filter"),
        help_text=_("fkey van de filter in FEWS unblobbed"),
        null=True, blank=True)

    lkey = models.IntegerField(
        verbose_name=_("Location"),
        help_text=_("lkey van de locatie in FEWS unblobbed"),
        null=True, blank=True)

    default_value = models.FloatField(verbose_name=_("default value"),
                                      null=True, blank=True,
                                      default=0.0)

    stick_to_last_value = models.NullBooleanField(verbose_name=_("reeks met 'geheugen'"),
                                      null=True, blank=True,
                                      help_text=_("moet een waarde geldig blijven tot de eerst volgende waarde (blok functie)"),
                                      default=False)

    def __unicode__(self):
        return self.name

    def get_last_event(self):
        """return event with latest datetime"""
        fews_timeseries = self._get_fews_timeserie_object()

        try:
            ts_events = fews_timeseries.timeseriedata.filter().order_by('-tsd_time')
            return ts_events[0]
        except:
            return None

    def _get_fews_timeserie_object(self):
        """

        """
        fews_parameter = FewsParameter.objects.get(pkey=self.pkey)
        fews_filter = FewsFilter.objects.get(id=self.fkey)
        fews_location = FewsLocation.objects.get(lkey=self.lkey)

        # the timestep is hardcoded for Waternet: "dag GMT+1" or "dag GMT-8"
        timestep = "dag GMT+1"
        try:
            fews_timeseries = FewsTimeserie.objects.get(
                timestep=timestep,
                parameterkey=fews_parameter,
                                                    filterkey=fews_filter,
                                                    locationkey=fews_location)
        except FewsTimeserie.DoesNotExist:
            timestep = "dag GMT-8"
            try:
                fews_timeseries = FewsTimeserie.objects.get(
                    timestep=timestep,
                    parameterkey=fews_parameter,
                    filterkey=fews_filter,
                    locationkey=fews_location)
            except FewsTimeserie.DoesNotExist:
                exception_msg = "No Fews time series exists with parameter key %d, filter key %d, location %d and timestep \"%s\"" % (self.pkey, self.fkey, self.lkey, timestep)
                logger.warning(exception_msg)
                raise IncompleteData(exception_msg)

        return fews_timeseries

    def events(self, start_date=None, end_date=None):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates. Which value is inserted depends on the values of
        self.stick_to_last_value and self.default.

        """
        fews_timeseries = self._get_fews_timeserie_object()

        ts_events = fews_timeseries.timeseriedata.filter().order_by('tsd_time')
        if not start_date is None:
            ts_events = ts_events.filter(tsd_time__gte=start_date)
        if not end_date is None:
            ts_events = ts_events.filter(tsd_time__lte=end_date)

        events = ((event.tsd_time, event.tsd_value) for event in ts_events)
        for date, value in generate_events(events, self.default_value,
                                           self.stick_to_last_value,
                                           start_date, end_date):
            if date is not None and value is not None:
                yield date, value


class Parameter(models.Model):
    """Identification of type of timeseries

    """

    TYPE_OTHER = 0
    TYPE_MEASURED = 1
    TYPE_USERINPUT = 2
    TYPE_COMPUTED = 3
    TYPE_REFERENCE = 4
    TYPES = ((TYPE_OTHER, 'overig'),
             (TYPE_MEASURED, 'gemeten'),
             (TYPE_USERINPUT, 'gebruikers invoer'),
             (TYPE_COMPUTED, 'berekend'))


    PARAMETER_OTHER = 0
    PARAMETER_WATERLEVEL = 1
    PARAMETER_CHLORIDE = 2
    PARAMETER_PRECIPITATION = 3
    PARAMETER_EVAPORATION = 4
    PARAMETER_SEEPAGE_INFILTRATION = 5
    PARAMETER_DISCHARGE = 6

    PARAMETERS = ((PARAMETER_OTHER, 'overig'),
                  (PARAMETER_WATERLEVEL, 'waterpeil'),
                  (PARAMETER_CHLORIDE, 'chloride'),
                  (PARAMETER_PRECIPITATION, 'neerslag'),
                  (PARAMETER_EVAPORATION, 'verdamping'),
                  (PARAMETER_SEEPAGE_INFILTRATION, 'kwel/wegzijging'),
                  (PARAMETER_DISCHARGE, 'debiet'))

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam van parameter"),
                            max_length=64)

    slug = models.SlugField(verbose_name=_("code"),
                            editable=False,
                            help_text=_("vaste code voor referentie van programma"))

    unit = models.CharField(
        verbose_name=_("eenheid"), max_length=64, null=True, blank=True)

    sourcetype = models.IntegerField(choices=TYPES, default=TYPE_OTHER)
    parameter = models.IntegerField(choices=PARAMETERS, default=PARAMETER_OTHER)

    def __unicode__(self):
        return self.name

    @classmethod
    def related_to_calculated_timeseries(cls):
        """ Return parameters that are related to calculated
        timeseries.

        Filter out the parameters which are connected to a
        waterbalance timeserie with timestep and configuration.
        """
        wb_ts = WaterbalanceTimeserie.objects.exclude(
            timestep=None, configuration=None)

        return Parameter.objects.filter(
            waterbalancetimeserie__in=wb_ts).distinct()

    def save(self):
        self.slug = slugify(self.name)
        super(Parameter, self).save()

class WaterbalanceTimeserie(models.Model):
    """Implements a time series.

    The time series is stored in a FEWS unblobbed database or in the database
    of the current Django project.

    Instance variables:
      * name *
        name of the time series
      * use_fews *
        holds iff the time series is stored in a FEWS unblobbed database
      * fews_timeseries *
        link to the time series when stored in a FEWS unblobbed database
      * local_timeseries *
        link to the time series when stored in the database of the current
        Django project

    """
    TIMESTEP_DAY = 1
    TIMESTEP_MONTH = 2
    TIMESTEP_QUARTER = 3
    TIMESTEP_YEAR = 4
    TIMESTEP_CHOICES = [
        (TIMESTEP_DAY, 'day'),
        (TIMESTEP_MONTH, 'month'),
        (TIMESTEP_QUARTER, 'quarter'),
        (TIMESTEP_YEAR, 'year'),
        ]



    name = models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam om de tijdreeks eenvoudig te herkennen"),
        max_length=64, null=True, blank=True)

    parameter = models.ForeignKey('Parameter')

    use_fews = models.BooleanField(verbose_name=_("gebruik FEWS tijdreeks"),
                                   default=False)

    fews_timeseries = models.ForeignKey(
        TimeseriesFews,
        verbose_name=_("FEWS"),
        help_text=_("tijdreeks opgeslagen in FEWS unblobbed database"),
        null=True, blank=True, related_name='wb_fews')

    local_timeseries = models.ForeignKey(
        Timeseries,
        verbose_name=_("Waterbalans tijdserie"),
        help_text=_("tijdreeks opgeslagen in eigen database"),
        null=True, blank=True, related_name='wb_local')

    # Belongs to what configuration? Optional, but needed for
    # adapter/lizard-map.
    configuration = models.ForeignKey(
        'WaterbalanceConf', editable=False, null=True, blank=True,
        help_text='WaterbalanceConf, needed for adapter/lizard-map.')

    # Timestep is what it's supposed to be. It is metadata for
    # (calculated) timeseries.
    timestep = models.IntegerField(
        editable=False,
        choices=TIMESTEP_CHOICES, null=True, blank=True,
        help_text='Timestep. Optional metadata for (calculated) timeseries')

    hint_datetime_start = models.DateTimeField(
        editable=False,
        null=True, blank=True,
        help_text=('Hint for datetime start of timerange. '
                   'Filled in by automatic process.'))
    hint_datetime_end = models.DateTimeField(
        editable=False,
        null=True, blank=True,
        help_text=('Hint for datetime end of timerange. '
                   'Filled in by automatic process.'))

    class Meta:
        verbose_name = _("7 Waterbalans tijdseries")
        verbose_name_plural = _("7 Waterbalans tijdseries")
        unique_together = (("name", "parameter",
                            "configuration", "timestep"),
                           )

    def __unicode__(self):
        return self.name

    def get_timeseries(self):
        """Return the time series this WaterbalanceTimeserie refers to.

        This method does not retrieve the actual events of the time series. To
        retrieve the events you have to call the events method on the time
        series that is returned.

        """
        if self.use_fews:
            timeseries = self.fews_timeseries
        else:
            timeseries = self.local_timeseries
        return timeseries

    def get_last_event(self):
        """ return last event """
        if self.use_fews:
            timeseries = self.fews_timeseries.get_last_event()
        else:
            timeseries = self.local_timeseries.get_last_event()
        return timeseries

    def in_daterange(self, dt):
        """
        Check if datetime (not date) is in daterange of available data.

        Uses hint if available, else check real values.
        """
        if self.hint_datetime_start and self.hint_datetime_end:
            dt_min = self.hint_datetime_start
            dt_max = self.hint_datetime_end
            logger.debug('Found min/max dates (hinted): %s %s' % (
                    dt_min, dt_max))
        else:
            ts = self.get_timeseries()
            dt_range = ts.timeseries_events.aggregate(
                Min('time'), Max('time'))
            dt_min = dt_range['time__min']
            dt_max = dt_range['time__max']
            logger.debug('Found min/max dates (from data): %s %s' % (
                    dt_min, dt_max))
        return dt >= dt_min and dt <= dt_max

    @classmethod
    @transaction.commit_on_success()
    def create(cls, name, parameter, timeseries,
               configuration=None, timestep=None,
               hint_datetime_start=None, hint_datetime_end=None):
        """
        Create a local timeserie.

        Will replace existing combination of name, parameter,
        configuration and timestep.

        timeserie is a dict with key=datetime, value=value
        """
        existing_timeseries = WaterbalanceTimeserie.objects.filter(
            name=name,
            parameter=parameter,
            configuration=configuration,
            timestep=timestep)
        if existing_timeseries:
            for ex_wb_ts in existing_timeseries:
                ex_wb_ts.get_timeseries().delete()  # Removes events as well
                ex_wb_ts.delete()
            logger.info(
                'Replacing existing timeseries (%s %s %s %s)'
                % (name, parameter, configuration, timestep))
        logger.debug(
            'Creating waterbalance timeseries (%s, timestep=%d)...' % (
                name, timestep))
        ts_name = '%s (%s)' % (name, configuration)
        local_timeseries = Timeseries(name=ts_name[:64])
        local_timeseries.save()
        counter = 0
        counter_report = 1000
        for key, value in timeseries.items():
            local_timeseries.timeseries_events.create(
                time=key,
                value=value)
            counter += 1
            if counter % counter_report == 0:
                logger.debug('record %d' % counter)
                counter_report = min(counter * 2, 10000)
        wb_ts = WaterbalanceTimeserie(
            name=name,
            parameter=parameter,
            use_fews=False,
            configuration=configuration,
            timestep=timestep,
            local_timeseries=local_timeseries,
            hint_datetime_start=hint_datetime_start,
            hint_datetime_end=hint_datetime_end)
        wb_ts.save()
        logger.debug('Successfully created waterbalance timeseries.')
        return wb_ts

    def times_values(self, start_date, end_date):
        """
        Return times and values for matplotlib.

        TODO: will now crash on fews timeseries.
        """
        return self.get_timeseries().times_values(start_date, end_date)

    def linked_with_info(self):
        """ shows information about where timeserie is linked with"""

        #configuration
        result = ""
        for link in self.configuration_results.all():
            result += "resultaat van configuratie '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.configuration_references.all():
            result += "referentie van configuratie '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_waterlevel_measurement.all():
            result += "gemeten waterpeil van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_min_level.all():
            result += "minimumpeil van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_max_level.all():
            result += "maximumpeil van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_targetlevel.all():
            result += "streefpeil van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.configuration_evaporation.all():
            result += "verdamping van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.configuration_precipitation.all():
            result += "neerslag van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_seepage.all():
            result += "kwel van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_infiltration.all():
            result += "wegzijging van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_sewer.all():
            result += "rioleringsreeks van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_nutricalc_min.all():
            result += "nutricalc minimumreeks van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.open_water_nutricalc_incr.all():
            result += "nutricalc incrementele reeks van openwater '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.bucket_seepage.all():
            result += "kwel van bakje '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.bucket_results.all():
            result += "resultaat van bakje '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.pumping_station_result.all():
            result += "resultaat van kunstwerk '%s' (id:%i); "%(link.__unicode__(), link.id)

        for link in self.pump_line_timeserie.all():
            result += "resultaat van pomplijn '%s' (id:%i); "%(link.__unicode__(), link.id)

        return result


class OpenWater(models.Model):
    """Represents the *open water*.

    Instance variables:
    * surface -- surface in [m2]
    * minimum_level -- link to time series for minimum water level in [m]
    * maximum_level -- link to time series for maximum water level in [m]
    * target_level -- link to time series for target water level in [m]
    * seepage -- link to input time serie for *kwel* in [mm/day]

    To get to the buckets that have access to the current open water, use the
    implicit attribute 'buckets' which is a Manager for these buckets.

    To get to the pumps of the current open water, use the implicit attribute
    'pumping_stations', which is a Manager for these pumps.

    All results of the openwater are stored in de WaterbalanceConf

    """
    class Meta:
        verbose_name = _("4 Open water")

    name = models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam om het open water eenvoudig te herkennen"),
        max_length=64)
    surface = models.IntegerField(
        verbose_name=_("oppervlakte"),
        help_text=_("oppervlakte in vierkante meters"))
    bottom_height = models.FloatField(
        verbose_name=_("bodemhoogte"),
        help_text=_("bodemhoogte in meters boven NAP"))
    use_min_max_level_relative_to_meas = models.BooleanField(
        default=False,
        verbose_name=_("gebruik min en max peil t.o.v. gemeten peil"),
        help_text=_("bodemhoogte in meters boven NAP"))
    waterlevel_measurement = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("gemeten waterpeil"),
        help_text=_("gemeten waterpeil ten behoeve van minimum en maximumpeil"),
        null=True, blank=True, related_name='open_water_waterlevel_measurement')
    min_level_relative_to_measurement = models.FloatField(
        default=0.0,
        null=True, blank=True,
        verbose_name=_("minimum level t.o.v. peilmeting"),
        help_text=_("de afwijking in meter onder het gemeten peil"))
    max_level_relative_to_measurement = models.FloatField(
        default=0.0,
        null=True, blank=True,
        verbose_name=_("maximum level t.o.v. peilmeting"),
        help_text=_("de afwijking in meter onder het gemeten peil"))
    minimum_level = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("ondergrens"),
        help_text=_("tijdserie naar ondergrens peil in meters"),
        null=True, blank=True, related_name='open_water_min_level')
    maximum_level = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("bovengrens"),
        help_text=_("tijdserie naar bovengrens peil in meters"),
        null=True, blank=True, related_name='open_water_max_level')
    target_level = models.ForeignKey(
        WaterbalanceTimeserie,
        editable=False,
        verbose_name=_("streefpeil"),
        help_text=_("tijdserie met streefpeil in mNAP. Deze wordt niet gebruikt"),
        null=True, blank=True, related_name='open_water_targetlevel')
    init_water_level = models.FloatField(
        verbose_name=_("initiele waterstand"),
        help_text=_("initiele waterstand in meters"))

    precipitation = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("neerslag"),
        help_text=_("meetreeks neerslag in [mm/dag]"),
        related_name='configuration_precipitation')

    evaporation = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("verdamping"),
        help_text=_("meetreeks verdamping in [mm/dag]"),
        related_name='configuration_evaporation')

    seepage = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("kwel"),
        help_text=_("tijdserie naar kwel"),
        related_name='open_water_seepage')

    infiltration = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("wegzijging"),
        help_text=_("tijdserie naar kwel"),
        related_name='open_water_infiltration')

    sewer = models.ForeignKey(
        WaterbalanceTimeserie,
        null=True, blank=True,
        verbose_name=_("referentie riolerings reeks"),
        related_name='open_water_sewer')

    nutricalc_min = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("Nutricalc minimum belasting"),
        help_text=_("nutricalc resultaat met resultaten in mg/dag.\
        Als dit veld leeg is wordt de belasting voor uitspoeling van ongedraineerde en gedraineerde bakjes \
        berekend op basis van het concentraties en uitspoeldebiet."),
        null=True, blank=True,
        related_name='open_water_nutricalc_min')

    nutricalc_incr = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("Nutricalc incrementele belasting"),
        help_text=_("nutricalc resultaat met resultaten in mg/dag.\
        Als dit veld leeg is wordt de belasting voor uitspoeling van ongedraineerde en gedraineerde bakjes \
        berekend op basis van het concentraties en uitspoeldebiet."),
        null=True, blank=True,
        related_name='open_water_nutricalc_incr')

    def __unicode__(self):
        return self.name

    def retrieve_pumping_stations(self):
        return self.pumping_stations.all()

    def retrieve_intakes(self):
        """Return the list of intakes."""
        return [intake for intake in self.retrieve_pumping_stations() \
                if intake.into]

    def surface_in_ha(self):
        return float(self.surface)/10000

    def linked_with_configuration(self):
        return str(self.waterbalanceconf)

    def retrieve_incoming_timeseries(self, only_input=False):
        """Return the dictionary of intake to measured time series.

        Parameter:
          * only_input *
            If only_input holds, this method only returns the measured time
            series of those intakes that are not used for level control,
            otherwise this method returns the measured time series of all
            intakes.

        Note that the measured time series of an intake is the sum of the
        measured time series of its pump lines.

        """
        incoming_timeseries = {}
        for pumping_station in self.retrieve_pumping_stations():
            if pumping_station.into:
                if only_input and pumping_station.computed_level_control:
                    continue
                timeseries = pumping_station.retrieve_sum_timeseries()
                incoming_timeseries[pumping_station] = timeseries
        return incoming_timeseries

    def retrieve_outgoing_timeseries(self, only_input=False):
        """Return the dictionary of pump to measured time series.

        Parameter:
          * only_input *
            If only_input holds, this method only returns the measured time
            series of those pumps that are not used for level control,
            otherwise this method returns the measured time series of all
            pumps.

        Note that the measured time series of a pump is the sum of the measured
        time series of its pump lines.

        """
        outgoing_timeseries = {}
        for pumping_station in self.retrieve_pumping_stations():
            if not pumping_station.into:
                if only_input and pumping_station.computed_level_control:
                    continue
                timeseries = pumping_station.retrieve_sum_timeseries()
                outgoing_timeseries[pumping_station] = timeseries
        return outgoing_timeseries

    def retrieve_sewer(self, start_date, end_date):
        if self.sewer is None:
            return None
        timeseries = self.sewer.get_timeseries() #start_date, end_date
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)


    def retrieve_minimum_level(self, start_date, end_date):
        if self.use_min_max_level_relative_to_meas:
             min_level = TimeseriesWithMemoryStub()
             min_level.add_value(start_date, self.min_level_relative_to_measurement)
             return add_timeseries(min_level, self.waterlevel_measurement)
        else:
            return TimeseriesRestrictedStub(timeseries=self.minimum_level.get_timeseries(),
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_maximum_level(self, start_date, end_date):
        if self.use_min_max_level_relative_to_meas:
             max_level = TimeseriesWithMemoryStub()
             max_level.add_value(start_date, self.max_level_relative_to_measurement)
             return add_timeseries(max_level, self.waterlevel_measurement)
        else:
            return TimeseriesRestrictedStub(timeseries=self.maximum_level.get_timeseries(),
                                        start_date=start_date,
                                        end_date=end_date)


class Bucket(models.Model):
    """Represents a *bakje*.

    Instance variables:
    * name -- name to show to the user
    * surface -- surface in [m2]
    * is_collapsed -- holds if and only if the bucket is a single bucket
    * open_water -- link to the open water
    * indraft -- link to input time serie for *intrek*
    * drainage -- link to input time serie for drainage
    * seepage -- link to input time serie for *kwel* in [mm/day]
    * infiltration -- link to input time serie for *wegzijging*
    * flow_off -- link to input time serie for *afstroming*
    * computed_flow_off -- link to computed time serie for *afstroming*

    """
    class Meta:
        verbose_name = _("Bakje")
        verbose_name_plural = _("Bakjes")

    UNDRAINED_SURFACE = 0
    HARDENED_SURFACE = 1
    DRAINED_SURFACE = 2
    STEDELIJK_SURFACE = 3
    SURFACE_TYPES = (
        (UNDRAINED_SURFACE, _("ongedraineerd")),
        (HARDENED_SURFACE, _("verhard")),
        (DRAINED_SURFACE, _("gedraineerd")),
        (STEDELIJK_SURFACE, _("stedelijk"))
    )

    name = models.CharField(verbose_name=_("naam"),
                            max_length=MAXLENGTH_OPENWATER_NAME)

    # We couple a bucket to the open water although from a semantic point of
    # view, an open water should reference the buckets. However, this is the
    # usual way to implement a one-to-many relationship.
    open_water = models.ForeignKey(OpenWater,
                                   related_name='buckets')  #mooier als je deze naam niet zet, dan is het altijd consistent

    surface_type =  models.IntegerField(
        verbose_name=_("oppervlakte type"),
        choices=SURFACE_TYPES,
        default=UNDRAINED_SURFACE)
    surface = models.IntegerField(
        verbose_name=_("oppervlakte"),
        help_text=_("oppervlakte in vierkante meters"))

    seepage = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("kwel"),
        help_text=_("tijdserie naar kwel"),
        null=True, blank=True,
        related_name='bucket_seepage')

    results = models.ManyToManyField(
        WaterbalanceTimeserie,
        verbose_name=_("resultaten"),
        help_text=_("Berekeningsresultaten van een bakje"),
        null=True, blank=True,
        editable=False,
        related_name='bucket_results')

    # TODO these values are optional: change their definition accordingly
    porosity = models.FloatField(verbose_name=_("porositeit"))
    crop_evaporation_factor = models.FloatField(
        verbose_name=_("gewasverdampingsfactor"))
    min_crop_evaporation_factor = models.FloatField(
        verbose_name=_("minimum gewasverdampingsfactor"))

    drainage_fraction = models.FloatField(verbose_name=_("fractie uitspoel"))
    indraft_fraction = models.FloatField(verbose_name=_("fractie intrek"))

    max_water_level = models.FloatField(
        verbose_name=_("maximum waterstand"),
        help_text=_("maximum waterstand in meters"))

    equi_water_level = models.FloatField(
        verbose_name=_("equilibrium waterstand"),
        help_text=_("equilibrium waterstand in meters"))

    min_water_level = models.FloatField(
        verbose_name=_("minimum waterstand"),
        null=True, blank=True,
        help_text=_("minimum waterstand in meters"))

    init_water_level = models.FloatField(
        verbose_name=_("initiele waterstand"),
        help_text=_("initiele waterstand in meters"))

    external_discharge = models.IntegerField(
        verbose_name=_("Afvoer (naar extern)"),
        help_text=_("Afvoer (naar extern) in mm/dag"),
        default=0)

    upper_porosity = models.FloatField(
        verbose_name=("porositeit bovenste bakje"))
    upper_drainage_fraction = models.FloatField(
        verbose_name=_("fractie uitspoel bovenste bakje"))
    upper_indraft_fraction = models.FloatField(
        verbose_name=_("fractie intrek bovenste bakje"))
    upper_max_water_level = models.FloatField(
        verbose_name=_("maximum waterstand bovenste bakje"),
        help_text=_("maximum waterstand in meters"))

    upper_equi_water_level = models.FloatField(
        verbose_name=_("equilibrium waterstand bovenste bakje"),
        help_text=_("equilibrium waterstand in meters"))

    upper_min_water_level = models.FloatField(
        verbose_name=_("minimum waterstand bovenste bakje"),
        null=True, blank=True,
        help_text=_("minimum waterstand in meters"))

    upper_init_water_level = models.FloatField(
        verbose_name=_("initiele waterstand bovenste bakje"),
        help_text=_("initiele waterstand in meters"))


    # We may need to add time series to store the inputs in the the right
    # units. For example, chances are seepage is specified in cubic milimeters
    # per hour. Internally however, we will probably use cubic meters and it
    # could be handy to store these values explicitly.

    def __unicode__(self):
        return '%s - %s'%(self.open_water.name, self.name)

    def retrieve_seepage(self, start_date, end_date):
        exception_msg = ""
        if self.seepage is None:
            exception_msg = "No seepage is defined for bucket of waterbalance area %s" % self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.seepage.get_timeseries()#start_date, end_date
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def surface_in_ha(self):
        return float(self.surface)/10000

    def upper_bucket_info(self):

        info = ""

        info += "porositeit: %s, "%str(self.upper_porosity)
        info += "drainage factor: %s, "%str(self.upper_drainage_fraction)
        info += "intrek_factor: %s, "%str(self.upper_indraft_fraction)
        info += "max peil: %s, "%str(self.upper_max_water_level)
        info += "min peil: %s, "%str(self.upper_min_water_level)
        info += "initieel peil: %s"%str(self.upper_init_water_level)

        return info


    def lower_bucket_info(self):

        info = ""
        info += "porositeit: %s, "%str(self.porosity)
        info += "drainage factor: %s, "%str(self.drainage_fraction)
        info += "intrek_factor: %s, "%str(self.indraft_fraction)
        info += "max peil: %s, "%str(self.max_water_level)
        info += "min peil: %s, "%str(self.min_water_level)
        info += "initieel peil: %s"%str(self.init_water_level)

        return info

class SobekBucket(models.Model):
    """Represents a *bakje*.

    Instance variables:
    * name -- name to show to the user
    * surface -- surface in [m2]
    * is_collapsed -- holds if and only if the bucket is a single bucket
    * open_water -- link to the open water
    * indraft -- link to input time serie for *intrek*
    * drainage -- link to input time serie for drainage
    * seepage -- link to input time serie for *kwel* in [mm/day]
    * infiltration -- link to input time serie for *wegzijging*
    * flow_off -- link to input time serie for *afstroming*
    * computed_flow_off -- link to computed time serie for *afstroming*

    """
    class Meta:
        verbose_name = _("Sobek Bakje")
        verbose_name_plural = _("Sobek Bakjes")

    name = models.CharField(verbose_name=_("naam"), max_length=64)

    open_water = models.ForeignKey(OpenWater,
                                   related_name='sobekbuckets')  #mooier als je deze naam niet zet, dan is het altijd consistent

    surface_type =  models.IntegerField(
        verbose_name=_("oppervlakte type"),
        choices=Bucket.SURFACE_TYPES,
        default=Bucket.UNDRAINED_SURFACE)

    flow_off = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("tijdserie oppervlakte afstroom"),
        help_text=_("tijdserie met resultaat oppervlakte afstroom"),
        null=True, blank=True,
        related_name='sobekbucket_flow_off')

    drainage_indraft = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("tijdserie uitstroom en intrek"),
        help_text=_("tijdserie met resultaat grondwater uitstroom en intrek"),
        null=True, blank=True,
        related_name='sobekbucket_drainage_indraft')

    def __unicode__(self):
        return '%s - %s'%(self.open_water.name, self.name)

class PumpingStation(models.Model):
    """Represents a pump that pumps water into or out of the open water.

    Instance variables:
    * name -- name of the pumping station
    * open_water -- link to the OpenWater
    * into -- holds if and only if the pump pumps water into the open water
    * percentage -- percentage of water through this pump
    * computed_level_control -- holds if this pump can be used for computed level control

    If this pump pumps water into (out of) the open water, the percentage is
    the percentage of incoming water that is pumped into (out of) the open
    water.

    """
    class Meta:
        unique_together = (("open_water", "label"),)
        verbose_name = _("6 Kunstwerk")
        verbose_name_plural = _("6 Kunstwerken")

    name = models.CharField(
        max_length=64,
        verbose_name=_("naam"),
        help_text=_("naam van kunstwerk, bijvoorbeeld \"Inlaat C\" of "
                    "\"Gemaal D\""))
    open_water = models.ForeignKey(
        OpenWater,
        help_text=_("open water waar deze pomp bij hoort"),
        related_name='pumping_stations')

    label = models.ForeignKey(
        "Label",
        help_text=_("open water waar deze pomp bij hoort"),
        related_name='pumping_stations')

    into = models.BooleanField(
        verbose_name=_("ingaande stroom"),
        help_text=_("aangevinkt als en alleen als de pomp een inlaat is"))
    percentage = models.FloatField(
        verbose_name=_("percentage"),
        help_text=_("percentage inkomend of uitgaand water via deze pomp"))
    max_discharge = models.FloatField(
        verbose_name=_("max_capaciteit"),null=True, blank=True,
        help_text=_("maximale capaciteit voor peilhandhaving"))

    computed_level_control = models.BooleanField(
        verbose_name=_("berekend"),
        default=False,
        help_text=_("aangevinkt als en alleen als de pomp gebruikt "
                    "mag worden voor automatisch berekende peilhandhaving"))

    results = models.ManyToManyField(
        WaterbalanceTimeserie,
        verbose_name=_("resultaten"),
        null=True, blank=True,
        editable=False,
        help_text=_("Berekeningsresultaten van een kunstwerk"),
        related_name='pumping_station_result')

    def __unicode__(self):
        return self.name

    def retrieve_sum_timeseries(self):
        """Return the sum of the time series of each of its PumpLine(s)."""
        result = SparseTimeseriesStub()
        for pump_line in self.retrieve_pump_lines():
            result = add_timeseries(result, pump_line.retrieve_timeseries())
        return result

    def retrieve_pump_lines(self):
        return self.pump_lines.all()


class PumpLine(models.Model):
    """Represents a *pomplijn*.

    Instance variables:
      * name *
        name of the pump line to help the user identify a PumpLine
      * pumping_station *
        link to the pumping station to which this pumpline belongs
      * timeserie *
        link to the time serie that contains the data

    """
    class Meta:
        verbose_name = _("Pomplijn")
        verbose_name_plural = _("Pomplijnen")

    name = models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam om de pomplijn eenvoudig te herkennen"),
        max_length=64)

    pumping_station = models.ForeignKey(
        PumpingStation,
        verbose_name=_("Pomp"),
        help_text=_("pomp waartoe deze pomplijn behoort"),
        related_name='pump_lines')

    timeserie = models.ForeignKey(
        WaterbalanceTimeserie,
        verbose_name=_("Tijdreeks"),
        help_text=_("tijdreeks naar gepompte waarden"),
        related_name='pump_line_timeserie')

    def retrieve_timeseries(self):
        return self.timeserie.get_timeseries()

    def __unicode__(self):
        return self.name


class WaterbalanceScenario(models.Model):
    """scenario's of wb. And area can have multiple configurations (scenario's)

    """
    class Meta:
        verbose_name = _("2 Waterbalans scenario")
        verbose_name_plural = _("2 Waterbalans scenario's")
        ordering = ("order",)
        permissions = (
            ("see_not_public_scenarios", "Can see not public scenario's"),
        )

    name = models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam van het scenario"),
        max_length=80)
    slug = models.SlugField(
        help_text=_("naam om de URL te maken"),
        editable=False)
    public = models.BooleanField(
        verbose_name=_("publiek"),
        help_text=_("is scenario zichtbaar voor iedereen"))
    order = models.IntegerField(
        verbose_name=_("volgorde"),
        default=0,
        help_text=_("lager is eerder in de lijst"))
    active = models.BooleanField(
        verbose_name=_("Actief"),
        default=False,
        help_text=_("is scenario te kiezen"))

    def __unicode__(self):
        return unicode(self.name)


class WaterbalanceArea(gis_models.Model):
    """Represents the area of which we want to know the waterbalance.

    Instance variables:
      * name *
        name of the area to help the user identify the WaterbalanceArea
      * slug *
        unique name to construct the URL
      * description *
        general description of the area
      * precipitation *
        link to time series for *neerslag* in [mm/day]
      * evaporation *
        link to time series for *verdamping* in [mm/day]
      * chloride *
        link to time series for *chloride* in [mg/l/dag]
      * phosphate *
        link to time series for *fosfaat* in [mg/l/dag]
      * open_water *
        link to the OpenWater of the current area

    """
    class Meta:
        verbose_name = _("1 Waterbalans gebied")
        verbose_name_plural = _("1 Waterbalans gebieden")
        ordering = ("name",)

    name = gis_models.CharField(
        verbose_name=_("naam"),
        help_text=_("naam om het waterbalans gebied te identificeren"),
        max_length=80)

    slug = gis_models.SlugField(
        editable=False,
        help_text=_("naam om de URL te maken"))

    #geom = gis_models.MultiPolygonField(
    #    'Region Border', srid=4326, null=True, blank=True)

    active = models.BooleanField(
        verbose_name=_("Actief"),
        default=False,
        help_text=_("is het gebied actief en te benaderen"))

    #objects = gis_models.GeoManager()

    def __unicode__(self):
        return unicode(self.name)


def load_shapefile(shapefile_name, name_field, source_epsg):
     """ Load shapefile into waterbalance areas and update geometry if name exist
     Instance variables:
   * shapefile_name *
     directory and name of shapefile (with Polygon or Multipolygon geometries)
   * name_field *
     header of field with the area names
   * source_epsg *
     coordinate sytem/ projection of shapefile (28992 = dutch projection

     """
     from osgeo import ogr  #, osr
     from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

     #original SRS
     oSRS=ogr.osr.SpatialReference()
     if source_epsg == 28992:
         #epsg28992 projection was defined incorrect in proj4, so define manually
         oSRS.ImportFromProj4("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs" )
     else:
         oSRS.ImportFromEPSG(source_epsg)

     #target SRS
     tSRS=ogr.osr.SpatialReference()
     tSRS.ImportFromEPSG(4326)
     poCT=ogr.osr.CoordinateTransformation(oSRS,tSRS)

     drv = ogr.GetDriverByName('ESRI Shapefile')
     source = drv.Open(str(shapefile_name))
     source_layer = source.GetLayer()

     if (source_layer.GetFeatureCount()>0):
         feature = source_layer.next()
         name_index = feature.GetFieldIndex(name_field)
         source_layer.ResetReading()

         for feature in source_layer:

             #krijgen van geometry
             geom = feature.GetGeometryRef()
             name = feature.GetField(name_index)
             if name == None:
                 logger.warning('warning, waterbalance area has no name')
                 name = 'none'
             geom.Transform(poCT)
             geometry = GEOSGeometry(geom.ExportToWkt(), srid=4326)
             if geometry.geom_type == 'Polygon':
                 geometry = MultiPolygon(geometry)
             wb_area, new = WaterbalanceArea.objects.get_or_create(name=name, defaults={'geom':geometry})
             if not new:

                 #update geometry
                 wb_area.geom = geometry
             else:
                 logger.debug('new area: %s'%name)
             wb_area.save()


class WaterbalanceConf(models.Model):
    """Represents the area of which we want to know the waterbalance.

    Instance variables:
      * name *
        name of the area to help the user identify the WaterbalanceArea
      * slug *
        unique name to construct the URL
      * description *
        general description of the area
      * precipitation *
        link to time series for *neerslag* in [mm/day]
      * evaporation *
        link to time series for *verdamping* in [mm/day]
      * open_water *
        link to the OpenWater of the current area

    """
    class Meta:
        unique_together = (("waterbalance_area", "waterbalance_scenario"),)
        verbose_name = _("3 Waterbalans configuratie")
        verbose_name_plural = _("3 Waterbalans configuraties")
        ordering = ("waterbalance_area__name", "waterbalance_scenario__order")

    waterbalance_area = models.ForeignKey(
        WaterbalanceArea,
        verbose_name=_("waterbalans gebied"))

    waterbalance_scenario = models.ForeignKey(
        WaterbalanceScenario,
        verbose_name=_("waterbalans scenario"))

    open_water = models.OneToOneField(OpenWater, null=True, blank=True, editable=False)

    description = models.TextField(null=True,
                                   blank=True,
                                   verbose_name="Beschrijving")

    calculation_start_date = models.DateTimeField(verbose_name=_("start datum berekening"),
                                                  help_text=_("vaste start datum van de berekening"))

    calculation_end_date = models.DateTimeField(verbose_name=_("eind datum berekening"),
                                                  help_text=_("vaste start datum van eind van de berekening (optioneel)"),
                                                  null=True,
                                                  blank=True)

    labels = models.ManyToManyField(
        "Label",
        through='Concentration',
        null=True, blank=True,
        verbose_name=_("Labels en concentraties"),
        help_text=_("Labels concentraties"),
        related_name='configuration_label')
    results = models.ManyToManyField(
        WaterbalanceTimeserie,
        null=True, blank=True,
        editable=False,
        verbose_name=_("resultaten"),
        help_text=_("Rekenresultaten"),
        related_name='configuration_results')
    references = models.ManyToManyField(
        WaterbalanceTimeserie,
        null=True, blank=True,
        verbose_name=_("referenties"),
        help_text=_("Berekeningsresultaten van een bakje"),
        related_name='configuration_references')

    def __unicode__(self):
        return unicode("%s - %s" % (self.waterbalance_area.name, self.waterbalance_scenario.name))

    @models.permalink
    def get_absolute_url(self):
        return ('waterbalance_area_summary', (),
                {'area_slug': str(self.waterbalance_area.slug),
                 'scenario_slug': str(self.waterbalance_scenario.slug)})

    def retrieve_precipitation(self, start_date, end_date):
        if self.open_water.precipitation is None:
            exception_msg = "No precipitation is defined for the waterbalance area %s" % self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.open_water.precipitation.get_timeseries() #start_date, end_date
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_evaporation(self, start_date, end_date):
        if self.open_water.evaporation is None:
            exception_msg = "No evaporation is defined for the waterbalance area %s" % self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.open_water.evaporation.get_timeseries() #start_date, end_date
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_seepage(self, start_date, end_date):
        open_water = self._retrieve_open_water() #start_date, end_date
        exception_msg = ""
        if open_water.seepage is None:
            exception_msg = "No seepage is defined for the open water of waterbalance area %s" % self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.open_water.seepage.get_timeseries()#start_date, end_date
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def get_calc_period(self, input_end_date_time=datetime.datetime.now()):
        """return calculation start_date and end_date """
        start_date = self.calculation_start_date
        if self.calculation_end_date:
            end_date = self.calculation_end_date
        else:
            #precipitation
            last_precipitation = self.open_water.precipitation.get_last_event()
            try:
                end_date = last_precipitation.time
            except AttributeError:
                end_date = last_precipitation.tsd_time
            #if last_precipitation:
            #    last_precipitation = last_precipitation.time
            #to do: else, warning
            #
            #
            #if input_end_date_time > last_precipitation:
            #    end_date = last_precipitation
            #else:
            #    end_date = input_end_date_time

        return start_date, end_date

    def _retrieve_open_water(self):
        exception_msg = ""
        if self.open_water is None:
            exception_msg = "No open water is defined for waterbalance area %s"% self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        return self.open_water

    def retrieve_buckets(self):
        open_water = self._retrieve_open_water()

        return open_water.buckets.all()


class Label(models.Model):
    """Specifies the labels of a water balance and their color.

    Instance variables:
    * name -- name of the group of parameters to which the parameter belongs
    * parent -- link to a possible parent label to specify a hierarchy
    * type -- incoming flow, outgoing flow or error flow
    * color -- hex code of the color that identifies the parameter group
    * order_index -- index to determine the order of the labels in a legend

    """

    class Meta:
        verbose_name = _("Label")
        verbose_name_plural = _("Labels")
        ordering = ('order', 'name', )



    TYPE_OTHER = 0
    TYPE_IN = 1
    TYPE_OUT = 2
    TYPE_ERROR = 3

    TYPES = ((TYPE_IN, 'in'),
             (TYPE_OUT, 'out'),
             (TYPE_ERROR, 'fout'),
             (TYPE_OTHER, 'overig'))


    name = models.CharField(max_length=64)
    program_name = models.CharField(max_length=64, null=True, blank=True)
    parent = models.ForeignKey('Label', null=True, blank=True)
    flow_type = models.IntegerField(choices=TYPES, default=TYPE_OTHER)

    order = models.IntegerField(
        verbose_name=_("volgorde"),
        default=0,
        help_text=_("lager is eerder in de lijst"))

    color = ColorField()
    color_increment = ColorField()

    def __unicode__(self):
        return self.name


class Concentration(models.Model):
    """Specifies the type, name and concentrations of a specific substance.

    Instance variables:
    * substance -- name of the substance
    * flow_name -- name of the flow to which the concentration applies
    * minimum -- minimum concentration in [mg/m3]
    * increment -- maximum allowed concentration above the minimum in [mg/m3]
    * area -- WaterbalanceArea for which this concentration is defined

    """
    class Meta:
        unique_together = (("configuration", "label"),)
        verbose_name = _("Concentratie")
        verbose_name_plural = _("Concentraties")

    label = models.ForeignKey("Label", related_name='label_concentrations',
        verbose_name=_("Label"))
    configuration = models.ForeignKey(
        WaterbalanceConf, related_name='config_concentrations',
        verbose_name=_("Waterbalans configuratie"))
    stof_lower_concentration = models.FloatField(
            verbose_name=_("stof ondergrens"),
            default=0.0,
            help_text=_("minimum concentratie in [mg/l]"))
    stof_increment  = models.FloatField(
            verbose_name=_("stof incrementeel"),
            default=0.0,
            help_text=_("incerementele concentratie in [mg/l]"))
    cl_concentration = models.FloatField(
            verbose_name=_("chloride concentratie"),
            default=0.0,
            help_text=_("increment t.o.v. minimum concentratie in [mg/l]"))
    p_lower_concentration = models.FloatField(
            editable = False, #even uitgezet. deze is gelijk aan stof
            verbose_name=_("P ondergrens"),
            default=0.0,
            help_text=_("minimum concentratie in [mg/l]"))
    p_incremental = models.FloatField(
            editable = False, #even uitgezet. deze is gelijk aan stof
            verbose_name=_("P increment"),
            default=0.0,
            help_text=_("increment t.o.v. minimum concentratie in [mg/l]"))
    n_lower_concentration = models.FloatField(
            verbose_name=_("N ondergrens"),
            blank=True, null=True,
            help_text=_("minimum concentratie in [mg/l]"))
    n_incremental = models.FloatField(
            verbose_name=_("N increment"),
            blank=True, null=True,
            help_text=_("increment t.o.v. minimum concentratie in [mg/l]"))
    so4_lower_concentration = models.FloatField(
            verbose_name=_("SO4 ondergrens"),
            blank=True, null=True,
            help_text=_("minimum concentratie in [mg/l]"))
    so4_incremental = models.FloatField(
            verbose_name=_("SO4 increment"),
            blank=True, null=True,
            help_text=_("increment t.o.v. minimum concentratie in [mg/l]"))

    def __unicode__(self):
        return "%s - %s" % (self.configuration.__unicode__(), self.label.name)

#@receiver(pre_save, sender=Parameter) #werkt pas vanaf versie 1.3
def pre_save_slug(*args, **kwargs):
    logger.debug('created slug for %s'%str(kwargs['instance'].name))
    kwargs['instance'].slug = slugify(kwargs['instance'].name)

def pre_save_configuration(*args, **kwargs):
    logger.debug('created slug for %s'%str(kwargs['instance'].__unicode__()))
    config = kwargs['instance']
    if kwargs['instance'].open_water == None:
        dummy_parameter, new = Parameter.objects.get_or_create(name='dummy')
        dummy_timeserie, new = WaterbalanceTimeserie.objects.get_or_create(name='selecteer', parameter=dummy_parameter)

        open_water = OpenWater()
        open_water.name = kwargs['instance'].__unicode__()[:MAXLENGTH_OPENWATER_NAME-1]
        open_water.bottom_height = -999.0
        open_water.surface = 9999.0

        open_water.maximum_level = dummy_timeserie
        open_water.minimum_level = dummy_timeserie

        open_water.target_level = dummy_timeserie
        open_water.init_water_level = -999.0
        open_water.precipitation = dummy_timeserie
        open_water.evaporation = dummy_timeserie
        open_water.seepage = dummy_timeserie
        open_water.infiltration = dummy_timeserie
        open_water.save()
        kwargs['instance'].open_water = open_water
    query = Label.objects.filter(flow_type=Label.TYPE_IN)
    if kwargs['instance'].id is not None:
        query = query.exclude(configuration_label__id=kwargs['instance'].id)

        for label in query:
            concentration, new = Concentration.objects.get_or_create(label=label, configuration=config)

        try:

            label = Label.objects.get(program_name='initial')
            concentration, new = Concentration.objects.get_or_create(label=label, configuration=config)
        except Label.DoesNotExist:
            pass

pre_save.connect(pre_save_slug, sender=Parameter)
pre_save.connect(pre_save_slug, sender=WaterbalanceArea)
pre_save.connect(pre_save_slug, sender=WaterbalanceScenario)
pre_save.connect(pre_save_configuration, sender=WaterbalanceConf)
