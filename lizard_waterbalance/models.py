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

from lizard_fewsunblobbed.models import Timeserie
from lizard_map.models import ColorField

from south.modelsinspector import add_ignored_fields
add_ignored_fields(["^lizard_map\.models\.ColorField"])

# Create your models here.


class WaterbalanceTimeserie(models.Model):
    """Connects time series to a WaterbalanceLabel.

    Instance variables:
    * label -- link to the WaterbalanceLabel that describes the time serie
    * volume -- link to the volume time serie data
    * chloride -- link to the chloride time serie data
    * phosphate -- link to the phosphate time serie data
    * nitrate -- link to the nitrate time serie data
    * sulfate -- link to the sulfate time serie data

    """
    label = models.ForeignKey('WaterbalanceLabel')
    volume = models.ForeignKey(Timeserie, related_name='+')
    chloride = models.ForeignKey(Timeserie, related_name='+')
    phosphate = models.ForeignKey(Timeserie, related_name='+')
    nitrate = models.ForeignKey(Timeserie, related_name='+')
    sulfate = models.ForeignKey(Timeserie, related_name='+')


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
    SURFACE_TYPES = (
        (UNDRAINED_SURFACE, _("ongedraineerd")),
        (HARDENED_SURFACE, _("verhard")),
        (DRAINED_SURFACE, _("gedraineerd")),
        )

    name = models.CharField(verbose_name=_("naam"), max_length=64)
    slug = models.CharField(verbose_name=_("slug"), max_length=64)

    surface_type =  models.IntegerField(verbose_name=_("oppervlakte type"),
                                        choices=SURFACE_TYPES,
                                        default=UNDRAINED_SURFACE)
    surface = models.IntegerField(verbose_name=_("oppervlakte"),
                                  help_text=_("oppervlakte in vierkante meters"))

    seepage = models.ForeignKey(WaterbalanceTimeserie,
                                verbose_name=_("kwel"),
                                help_text=_("tijdserie naar kwel"),
                                null=True, blank=True,
                                related_name='+')

    porosity = models.FloatField(verbose_name=_("porositeit"))
    crop_evaporation_factor = models.FloatField(verbose_name=_("gewasverdampingsfactor"))
    min_crop_evaporation_factor = models.FloatField(verbose_name=_("minimum gewasverdampingsfactor"))

    drainage_fraction = models.FloatField(verbose_name=_("fractie uitspoel"))
    infiltration_fraction = models.FloatField(verbose_name=_("fractie intrek"))

    max_water_level = models.FloatField(verbose_name=_("maximum waterstand"),
                                        help_text=_("maximum waterstand in meters"))

    equi_water_level = models.FloatField(verbose_name=_("equilibrium waterstand"),
                                         help_text=_("equilibrium waterstand in meters"))

    min_water_level = models.FloatField(verbose_name=_("minimum waterstand"),
                                        help_text=_("minimum waterstand in meters"))

    init_water_level = models.FloatField(verbose_name=_("initiele waterstand"),
                                         help_text=_("initiele waterstand in meters"))

    external_discharge = models.IntegerField(verbose_name=_("Afvoer (naar extern)"),
                                             help_text=_("Afvoer (naar extern) in mm/dag"),
                                             default=0)

    upper_porosity = models.FloatField(verbose_name=("porositeit bovenste bakje"))
    upper_crop_evaporation_factor = models.FloatField(verbose_name=_("gewasverdampingsfactor bovenste bakje"))
    upper_min_crop_evaporation_factor = models.FloatField(verbose_name=_("minimum gewasverdampingsfactor bovenste bakje"))

    # We couple a bucket to the open water although from a semantic point of
    # view, an open water should reference the buckets. However, this is the
    # usual way to implement a one-to-many relationship.
    open_water = models.ForeignKey("Bucket",
                                   null=True,
                                   blank=True,
                                   related_name='buckets')

    indraft = models.ForeignKey(WaterbalanceTimeserie,
                                verbose_name=_("intrek"),
                                help_text=_("tijdserie naar intrek"),
                                null=True,
                                blank=True,
                                related_name='+')
    drainage = models.ForeignKey(WaterbalanceTimeserie,
                                 verbose_name=_("drainage"),
                                 help_text=_("tijdserie naar drainage"),
                                 null=True,
                                 blank=True,
                                 related_name='+')
    computed_seepage = models.ForeignKey(WaterbalanceTimeserie,
                                         verbose_name=_("berekende kwel"),
                                         help_text=_("tijdserie naar berekende kwel"),
                                         null=True,
                                         blank=True,
                                         related_name='+')
    infiltration = models.ForeignKey(WaterbalanceTimeserie,
                                     verbose_name=_("wegzijging"),
                                     help_text=_("tijdserie naar wegzijging"),
                                     null=True,
                                     blank=True,
                                     related_name='+')
    flow_off = models.ForeignKey(WaterbalanceTimeserie,
                                 verbose_name=_("afstroming"),
                                 help_text=_("tijdserie naar afstroming"),
                                 null=True,
                                 blank=True,
                                 related_name='+')
    computed_flow_off = \
        models.ForeignKey(WaterbalanceTimeserie,
                          verbose_name=_("berekende afstroming"),
                          help_text=_("tijdserie naar berekende afstroming"),
                          null=True,
                          blank=True,
                          related_name='+')

    # We may need to add time series to store the inputs in the the right
    # units. For example, chances are seepage is specified in cubic milimeters
    # per hour. Internally however, we will probably use cubic meters and it
    # could be handy to store these values explicitly.

    def __unicode__(self):
        return self.slug

class OpenWater(Bucket):
    """Represents an *open water(bakje)*.

    Instance variables:
    * minimum_level -- link to time series for minimum water level in [m]
    * maximum_level -- link to time series for maximum water level in [m]
    * target_level -- link to time series for target water level in [m]
    * sluice_error -- link to computed time series for model errors

    To get to the buckets that have access to the current open water, use the
    implicit attribute 'buckets' which is a Manager for these buckets.

    To get to the pumps of the current open water, use the implicit attribute
    'pumping_stations', which is a Manager for these pumps.

    """
    minimum_level = models.ForeignKey(WaterbalanceTimeserie,
                                      verbose_name=_("ondergrens"),
                                      help_text=_("tijdserie naar ondergrens peil in meters"),
                                      null=True,
                                      blank=True,
                                      related_name='+')
    maximum_level = models.ForeignKey(WaterbalanceTimeserie,
                                      verbose_name=_("bovengrens"),
                                      help_text=_("tijdserie naar bovengrens peil in meters"),
                                      null=True,
                                      blank=True,
                                      related_name='+')
    target_level = models.ForeignKey(WaterbalanceTimeserie,
                                     verbose_name=_("streefpeil"),
                                     help_text=_("tijdserie met streefpeil in meters"),
                                     null=True,
                                     blank=True,
                                     related_name='+')
    sluice_error = models.ForeignKey(WaterbalanceTimeserie,
                                     verbose_name=_("sluitfout"),
                                     help_text=_("tijdserie met sluitfout"),
                                     null=True,
                                     blank=True,
                                     related_name='+')


class PumpingStation(models.Model):
    """Represents a pump that pumps water into or out of the open water.

    Instance variables:
    * name -- name of the pumping station
    * open_water -- link to the OpenWater
    * into -- holds if and only if the pump pumps water into the open water
    * percentage -- percentage of water through this pump

    If this pump pumps water into (out of) the open water, the percentage is
    the percentage of incoming water that is pumped into (out of) the open
    water.

    """
    class Meta:
        verbose_name = _("Pomp")
        verbose_name_plural = _("Pompen")

    name = models.CharField(max_length=64,
                            verbose_name=_("naam"),
                            help_text=_("naam van de pomp, bijvoorbeeld \"Inlaat C\" of \"Gemaal D\""))
    open_water = models.ForeignKey(OpenWater,
                                   help_text=_("open water waar deze pomp bij hoort"),
                                   related_name='pumping_stations')
    into = models.BooleanField(verbose_name=_("ingaande stroom"),
                               help_text=_("aangevinkt als en alleen als de pomp een inlaat is"))
    percentage = models.FloatField(verbose_name=_("percentage"),
                                   help_text=_("percentage inkomend of uitgaand water via deze pomp"))


class PumpLine(models.Model):
    """Represents a *pomplijn*.

    Instance variables:
    * pump -- link to the pump to which this pumpline belongs
    * timeserie -- link to the time serie that contains the data

    """
    class Meta:
        verbose_name = _("Pomplijn")
        verbose_name_plural = _("Pomplijnen")

    pump = models.ForeignKey(PumpingStation, related_name='pump_lines')
    timeserie = models.ForeignKey(WaterbalanceTimeserie, related_name='+')


class WaterbalanceArea(models.Model):
    """Represents the area of which we want to know the waterbalance.

    Instance variables:
    * name -- name to show to the user
    * slug -- unique name to construct the URL
    * description -- general description
    * precipitation -- link to time series for *neerslag* in [mm/day]
    * evaporation -- link to time series for *verdamping* in [mm/day]

    """
    class Meta:
        verbose_name = _("Waterbalans gebied")
        verbose_name_plural = _("Waterbalans gebieden")
        ordering = ("name",)

    name = models.CharField(max_length=80)
    slug = models.SlugField(help_text=_("Name to construct the URL."))
    description = models.TextField(null=True,
                                   blank=True,
                                   help_text="You can use markdown")

    precipitation = models.ForeignKey(WaterbalanceTimeserie,
                                      related_name='+',
                                      null=True,
                                      blank=True)
    evaporation = models.ForeignKey(WaterbalanceTimeserie,
                                    related_name='+',
                                    null=True,
                                    blank=True)
    open_water = models.ForeignKey(OpenWater, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('krw_waternet.waterbalance', (), {'area': str(self.slug)})


class WaterbalanceLabel(models.Model):
    """Specifies the labels of a water balance and their color.

    Instance variables:
    * name -- name of the group of parameters to which the parameter belongs
    * parent -- link to a possible parent label to specify a hierarchy
    * type -- incoming flow, outgoing flow or error flow
    * color -- hex code of the color that identifies the parameter group
    * order_index -- index to determine the order of the labels in a legend

    """

    class Meta:
        verbose_name = _("Waterbalans label")
        verbose_name_plural = _("Waterbalans labels")
        ordering = ("order_index",)

    TYPE_IN = 1
    TYPE_OUT = 2
    TYPE_ERROR = 3

    TYPES = ((TYPE_IN, 'in'), (TYPE_OUT, 'out'), (TYPE_ERROR, 'fout'))

    name = models.CharField(max_length=64)
    parent = models.ForeignKey('WaterbalanceLabel', null=True, blank=True)
    flow_type = models.IntegerField(choices=TYPES, default=TYPE_IN)
    color = ColorField()
    order_index = models.IntegerField(unique=True)

    def __unicode__(self):
        return self.name
