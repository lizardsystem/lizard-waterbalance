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
from datetime import timedelta

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db import models
from django.utils.translation import ugettext as _

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie
from lizard_map.models import ColorField

from south.modelsinspector import add_ignored_fields
add_ignored_fields(["^lizard_map\.models\.ColorField"])

from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import TimeseriesRestrictedStub
from timeseries.timeseriesstub import TimeseriesStub

from django.db import transaction

logger = logging.getLogger(__name__)

# Create your models here.

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
    class Meta:
        verbose_name = _("Tijdreeks")
        verbose_name_plural = _("Tijdreeksen")

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam om de tijdreeks eenvoudig te herkennen"),
                            max_length=64, null=True, blank=True)


    def raw_events(self):
        """Return a generator to iterate over all events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function does
        not fill in the missing dates with value.

        """
        for event in self.timeseries_events.all():
            yield event.time, event.value

    def events(self):
        """Return a generator to iterate over all daily events.

        The generator iterates over the events in the order they were added. If
        dates are missing in between two successive events, this function fills
        in the missing dates with the value on the latest known date.

        """
        date_to_yield = None # we initialize this variable to silence pyflakes
        previous_value = 0
        for event in self.timeseries_events.all():
            date = event.time
            value = event.value
            if not date_to_yield is None:
                while date_to_yield < date:
                    yield date_to_yield, previous_value
                    date_to_yield = date_to_yield + timedelta(1)
            yield date, value
            previous_value = value
            date_to_yield = date + timedelta(1)

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
        verbose_name = _("tijdreeks FEWS")
        verbose_name_plural = _("tijdreeksen FEWS")

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam om de tijdreeks eenvoudig te herkennen"),
                            max_length=64, null=True, blank=True)

    pkey = models.IntegerField(verbose_name=_("Parameter"),
                               help_text=_("pkey van de parameter in FEWS unblobbed"),
                               null=True, blank=True)

    fkey = models.IntegerField(verbose_name=_("Filter"),
                               help_text=_("fkey van de filter in FEWS unblobbed"),
                               null=True, blank=True)

    lkey = models.IntegerField(verbose_name=_("Location"),
                               help_text=_("lkey van de locatie in FEWS unblobbed"),
                               null=True, blank=True)

    def __unicode__(self):
        return self.name

    def events(self):
        """Return a generator to iterate over all events.

        The generator iterates over the events earliest date first.

        """
        fews_parameter = Parameter.objects.get(pkey=self.pkey)
        fews_filter = Filter.objects.get(id=self.fkey)
        fews_location = Location.objects.get(lkey=self.lkey)

        # the timestep is hardcoded for Waternet: "dag GMT+1" or "dag GMT-8"
        timestep = "dag GMT+1"
        try:
            fews_timeseries = Timeserie.objects.get(timestep=timestep,
                                                    parameterkey=fews_parameter,
                                                    filterkey=fews_filter,
                                                    locationkey=fews_location)
        except Timeserie.DoesNotExist:
            timestep = "dag GMT-8"
            try:
                fews_timeseries = Timeserie.objects.get(timestep=timestep,
                                                        parameterkey=fews_parameter,
                                                        filterkey=fews_filter,
                                                        locationkey=fews_location)
            except Timeserie.DoesNotExist:
                exception_msg = "No Fews time series exists with parameter key %d, filter key %d, location %d and timestep \"%s\"" % (self.pkey, self.fkey, self.lkey, timestep)
                logger.warning(exception_msg)
                raise IncompleteData(exception_msg)

        for event in fews_timeseries.timeseriedata.all().order_by('tsd_time'):
            yield event.tsd_time, event.tsd_value


class Parameter(models.Model):
    """Identification of type of timeseries

    """
    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam van parameter"),
                            max_length=64)
    unit = models.CharField(verbose_name=_("eenheid"), max_length=64, null=True, blank=True)

    def __unicode__(self):
        return self.name
    
    
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
      * label *
        link to the WaterbalanceLabel that describes the time serie

    """
    class Meta:
        verbose_name = _("Waterbalans tijdreeks")
        verbose_name_plural = _("Waterbalans tijdreeksen")

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam om de tijdreeks eenvoudig te herkennen"),
                            max_length=64, null=True, blank=True)

    parameter = models.ForeignKey('Parameter', related_name='+')

    label = models.ForeignKey('WaterbalanceLabel', null=True, blank=True)

    use_fews = models.BooleanField(verbose_name=_("gebruik FEWS tijdreeks"))

    fews_timeseries = models.ForeignKey(TimeseriesFews,
                                    verbose_name=_("FEWS"),
                                    help_text=_("tijdreeks opgeslagen in FEWS unblobbed database"),
                                    null=True, blank=True, related_name='+')

    local_timeseries = models.ForeignKey(Timeseries,
                               verbose_name=_("standaard"),
                               help_text=_("tijdreeks opgeslagen in eigen database"),
                               null=True, blank=True, related_name='+')

    def get_timeseries(self):
        """Returns the time series this WaterbalanceTimeserie refers to."""
        if self.use_fews:
            timeseries = self.fews_timeseries
        else:
            timeseries = self.local_timeseries
        return timeseries

    def __unicode__(self):
        return self.name

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
        verbose_name = _("Open water")

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam om het open water eenvoudig te herkennen"),
                            max_length=64)
    surface = models.IntegerField(verbose_name=_("oppervlakte"),
                                  help_text=_("oppervlakte in vierkante meters"))
    bottom_height = models.FloatField(verbose_name=_("bodemhoogte"),
                                      help_text=_("bodemhoogte in meters boven NAP"),
                                      null=True, blank=True)
    minimum_level = models.ForeignKey(WaterbalanceTimeserie,
                                      verbose_name=_("ondergrens"),
                                      help_text=_("tijdserie naar ondergrens peil in meters"),
                                      null=True, blank=True, related_name='open_water_min_level')
    maximum_level = models.ForeignKey(WaterbalanceTimeserie,
                                      verbose_name=_("bovengrens"),
                                      help_text=_("tijdserie naar bovengrens peil in meters"),
                                      null=True, blank=True, related_name='open_water_max_level')
    target_level = models.ForeignKey(WaterbalanceTimeserie,
                                     verbose_name=_("streefpeil"),
                                     help_text=_("tijdserie met streefpeil in meters"),
                                     null=True, blank=True, related_name='open_water_targetlevel')
    init_water_level = models.FloatField(verbose_name=_("initiele waterstand"),
                                         help_text=_("initiele waterstand in meters"))

    seepage = models.ForeignKey(WaterbalanceTimeserie,
                                verbose_name=_("kwel"),
                                help_text=_("tijdserie naar kwel"),
                                null=True, blank=True, related_name='open_water_seepage')    

    infiltration = models.ForeignKey(WaterbalanceTimeserie,
                                verbose_name=_("wegzijging"),
                                help_text=_("tijdserie naar kwel"),
                                null=True, blank=True, related_name='open_water_infiltration')  

    def __unicode__(self):
        return self.name

    def retrieve_pumping_stations(self):
        return self.pumping_stations.all()

    def retrieve_intakes(self):
        """Return the list of intakes."""
        return [intake for intake in self.retrieve_pumping_stations() \
                if intake.into]

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

    def retrieve_minimum_level(self):
        return self.minimum_level.get_timeseries()

    def retrieve_maximum_level(self):
        return self.maximum_level.get_timeseries()

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
                                related_name='bucket_seepage')
 
    
    results = models.ManyToManyField(WaterbalanceTimeserie, 
                                     verbose_name=_("resultaten"),
                                     help_text=_("Berekeningsresultaten van een bakje"),
                                     null=True, blank=True,
                                     related_name='bucket_results')

    # TODO these values are optional: change their definition accordingly
    porosity = models.FloatField(verbose_name=_("porositeit"))
    crop_evaporation_factor = models.FloatField(verbose_name=_("gewasverdampingsfactor"))
    min_crop_evaporation_factor = models.FloatField(verbose_name=_("minimum gewasverdampingsfactor"))

    drainage_fraction = models.FloatField(verbose_name=_("fractie uitspoel"))
    indraft_fraction = models.FloatField(verbose_name=_("fractie intrek"))

    max_water_level = models.FloatField(verbose_name=_("maximum waterstand"),
                                        help_text=_("maximum waterstand in meters"))

    equi_water_level = models.FloatField(verbose_name=_("equilibrium waterstand"),
                                         help_text=_("equilibrium waterstand in meters"))

    min_water_level = models.FloatField(verbose_name=_("minimum waterstand"),
                                        null=True, blank=True,
                                        help_text=_("minimum waterstand in meters"))

    init_water_level = models.FloatField(verbose_name=_("initiele waterstand"),
                                         help_text=_("initiele waterstand in meters"))

    external_discharge = models.IntegerField(verbose_name=_("Afvoer (naar extern)"),
                                             help_text=_("Afvoer (naar extern) in mm/dag"),
                                             default=0)

    upper_porosity = models.FloatField(verbose_name=("porositeit bovenste bakje"))
    upper_drainage_fraction = models.FloatField(verbose_name=_("fractie uitspoel bovenste bakje"))
    upper_indraft_fraction = models.FloatField(verbose_name=_("fractie intrek bovenste bakje"))
    upper_max_water_level = models.FloatField(verbose_name=_("maximum waterstand bovenste bakje"),
                                        help_text=_("maximum waterstand in meters"))

    upper_equi_water_level = models.FloatField(verbose_name=_("equilibrium waterstand bovenste bakje"),
                                         help_text=_("equilibrium waterstand in meters"))

    upper_min_water_level = models.FloatField(verbose_name=_("minimum waterstand bovenste bakje"),
                                        null=True, blank=True,
                                        help_text=_("minimum waterstand in meters"))

    upper_init_water_level = models.FloatField(verbose_name=_("initiele waterstand bovenste bakje"),
                                         help_text=_("initiele waterstand in meters"))

    # We couple a bucket to the open water although from a semantic point of
    # view, an open water should reference the buckets. However, this is the
    # usual way to implement a one-to-many relationship.
    open_water = models.ForeignKey(OpenWater,
                                   null=True,
                                   blank=True,
                                   related_name='buckets') #mooier als je deze naam niet zet, dan is het altijd consistent

    # We may need to add time series to store the inputs in the the right
    # units. For example, chances are seepage is specified in cubic milimeters
    # per hour. Internally however, we will probably use cubic meters and it
    # could be handy to store these values explicitly.

    def __unicode__(self):
        return self.slug


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
        verbose_name = _("Pomp")
        verbose_name_plural = _("Pompen")

    name = models.CharField(max_length=64,
                            verbose_name=_("naam"),
                            help_text=_("naam van de pomp, bijvoorbeeld \"Inlaat C\" of \"Gemaal D\""))
    open_water = models.ForeignKey(OpenWater, null=True, blank=True,
                                   help_text=_("open water waar deze pomp bij hoort"),
                                   related_name='pumping_stations')
    into = models.BooleanField(verbose_name=_("ingaande stroom"),
                               help_text=_("aangevinkt als en alleen als de pomp een inlaat is"))
    percentage = models.FloatField(verbose_name=_("percentage"),
                                   help_text=_("percentage inkomend of uitgaand water via deze pomp"))
    max_discharge = models.FloatField(verbose_name=_("max_capaciteit"),null=True,
                                   help_text=_("maximale capaciteit voor peilhandhaving"))
    
    computed_level_control = models.BooleanField(verbose_name=_("berekend"),
                                                 default=False,
                                                 help_text=_("aangevinkt als en alleen als de pomp gebruikt mag worden voor automatisch berekende peilhandhaving"))

    results = models.ManyToManyField(WaterbalanceTimeserie, 
                                     verbose_name=_("resultaten"),
                                     null=True, blank=True,
                                     help_text=_("Berekeningsresultaten van een kunstwerk"),
                                     related_name='pumping_station_result')
        
    def __unicode__(self):
        return self.name

    def retrieve_sum_timeseries(self):
        """Return the sum of the time series of each of its PumpLine(s)."""
        result = TimeseriesStub()
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

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam om de pomplijn eenvoudig te herkennen"),
                            max_length=64, null=True, blank=True)

    pumping_station = models.ForeignKey(PumpingStation,
                                        verbose_name=_("Pomp"),
                                        help_text=_("pomp waartoe deze pomplijn behoort"),
                                        related_name='pump_lines')

    timeserie = models.ForeignKey(WaterbalanceTimeserie,
                                  verbose_name=_("Tijdreeks"),
                                  help_text=_("tijdreeks naar gepompte waarden"),
                                  null=True, blank=True, related_name='pump_line_timeserie')

    def retrieve_timeseries(self):
        return self.timeserie.get_timeseries()

    def __unicode__(self):
        return self.name


class WaterbalanceScenario(models.Model):
    """scenario's of wb. And area can have multiple configurations (scenario's)

    """
    class Meta:
        verbose_name = _("Waterbalans scenario")
        verbose_name_plural = _("Waterbalans scenario's")
        ordering = ("order",)

    name = models.CharField(verbose_name=_("naam"),
                            help_text=_("naam van het scenario"),
                            max_length=80)
    public = models.BooleanField(verbose_name=_("publiek"),
                                 help_text=_("is scenario zichtbaar in dashboards"))
    order = models.IntegerField(verbose_name=_("volgorde"),
                                default=0,
                                help_text=_("lager is eerder in de lijst"))

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
        verbose_name = _("Waterbalans gebied")
        verbose_name_plural = _("Waterbalans gebieden")
        ordering = ("name",)

    name = gis_models.CharField(verbose_name=_("naam"),
                            help_text=_("naam om het waterbalans gebied te identificeren"),
                            max_length=80)

    slug = gis_models.SlugField(help_text=_("naam om de URL te maken"))
    geom = gis_models.MultiPolygonField('Region Border', srid=4326, null=True, blank=True)

    objects = gis_models.GeoManager()

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
     from osgeo import ogr, osr
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
                 print 'warning, waterbalance area has no name'
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
                 print 'new area: %s'%name
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
        verbose_name = _("Waterbalans configuratie")
        verbose_name_plural = _("Waterbalans configuraties")
        ordering = ("waterbalance_area__name", "waterbalance_scenario__order")

    waterbalance_area = models.ForeignKey(WaterbalanceArea,
                                          verbose_name=_("waterbalans gebied"))

    waterbalance_scenario = models.ForeignKey(WaterbalanceScenario,
                                          verbose_name=_("waterbalans scenario"))

    slug = models.SlugField(help_text=_("naam om de URL te maken"))

    open_water = models.ForeignKey(OpenWater, null=True, blank=True)

    description = models.TextField(null=True,
                                   blank=True,
                                   help_text="You can use markdown")

    precipitation = models.ForeignKey(WaterbalanceTimeserie,
                                      verbose_name=_("neerslag"),
                                      help_text=_("meetreeks neerslag in [mm/dag]"),
                                      related_name='configuration_precipitation',
                                      null=True,
                                      blank=True)
    evaporation = models.ForeignKey(WaterbalanceTimeserie,
                                    verbose_name=_("verdamping"),
                                    help_text=_("meetreeks verdamping in [mm/dag]"),
                                    related_name='configuration_evaporation',
                                    null=True,
                                    blank=True)
    
    results = models.ManyToManyField(WaterbalanceTimeserie,
                                     null=True, blank=True, 
                                     verbose_name=_("resultaten"),
                                     help_text=_("Rekenresultaten"),
                                     related_name='configuration_results')
    references = models.ManyToManyField(WaterbalanceTimeserie,
                                     null=True, blank=True,
                                     verbose_name=_("referenties"),
                                     help_text=_("Berekeningsresultaten van een bakje"),
                                     related_name='configuration_references')


    def __unicode__(self):
        return unicode("%s - %s" % (self.waterbalance_area.name, self.waterbalance_scenario.name))

    @models.permalink
    def get_absolute_url(self):
        return ('waterbalance_area_summary', (), {'area': str(self.slug)})

    def retrieve_precipitation(self, start_date, end_date):
        if self.precipitation is None:
            exception_msg = "No precipitation is defined for the waterbalance area %s" % self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.precipitation.get_timeseries() #start_date, end_date
        return TimeseriesRestrictedStub(timeseries=timeseries,
                                        start_date=start_date,
                                        end_date=end_date)

    def retrieve_evaporation(self, start_date, end_date):
        if self.evaporation is None:
            exception_msg = "No evaporation is defined for the waterbalance area %s" % self.__unicode__()
            logger.warning(exception_msg)
            raise IncompleteData(exception_msg)
        timeseries = self.evaporation.get_timeseries() #start_date, end_date
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

    TYPE_IN = 1
    TYPE_OUT = 2
    TYPE_ERROR = 3

    TYPES = ((TYPE_IN, 'in'), (TYPE_OUT, 'out'), (TYPE_ERROR, 'fout'))

    name = models.CharField(max_length=64)
    parent = models.ForeignKey('WaterbalanceLabel', null=True, blank=True)
    flow_type = models.IntegerField(choices=TYPES, default=TYPE_IN)
    color = ColorField()

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
        verbose_name = _("Concentratie")
        verbose_name_plural = _("Concentraties")

    SUBSTANCE_CHLORIDE = 0
    SUBSTANCE_PHOSPHATE = 1
    SUBSTANCES = ((SUBSTANCE_CHLORIDE, "chloride"),
                  (SUBSTANCE_PHOSPHATE, "fosfaat"))

    substance = models.IntegerField(choices=SUBSTANCES,
                                    default=SUBSTANCE_CHLORIDE,
                                    verbose_name=_("stof"))
    flow_name = models.CharField(max_length=64, verbose_name=_("naam"),
                                 help_text=_("naam van de waterstroom van deze concentratie"))
    minimum = models.FloatField(verbose_name=_("minimum"),
                                help_text=_("minimum concentratie in [mg/l]"))
    increment = models.FloatField(verbose_name=_("increment"),
                                  help_text=_("maximum extra concentratie boven het minimum in [mg/l]"),
                                  null=True, blank=True)
    configuration = models.ForeignKey(WaterbalanceConf, related_name='concentrations',
                                      verbose_name=_("Waterbalans configuratie"))

    def __unicode__(self):
        substance_name = next((substance[1] for substance in self.SUBSTANCES if substance[0] == self.substance), None)
        return u"%s - %s" % (unicode(substance_name), unicode(self.flow_name))


class WaterbalanceShape(gis_models.Model):
    """
    Viewer model for the Waterbalance shapefile.

    The shapefile was originally imported using shp2pgsql.
    """
    gid = gis_models.IntegerField(primary_key=True)
    gaf_gaf_id = gis_models.BigIntegerField()
    richting = gis_models.FloatField()
    temp_id = gis_models.CharField(max_length=24)
    objectid = gis_models.BigIntegerField()
    gaf_id = gis_models.IntegerField()
    gafident = gis_models.CharField(max_length=24)
    gaf_gaf__1 = gis_models.BigIntegerField()
    gafnaam = gis_models.CharField(max_length=50)
    gafsoort = gis_models.CharField(max_length=50)
    gafoppvl = gis_models.BigIntegerField()
    gafbemal = gis_models.SmallIntegerField()
    gafcode = gis_models.CharField(max_length=20)
    osmomsch = gis_models.CharField(max_length=60)
    iws_legrt = gis_models.BigIntegerField()
    ha = gis_models.DecimalField(max_digits=1000, decimal_places=1000)
    ha_int = gis_models.IntegerField()
    hectare = gis_models.DecimalField(max_digits=1000, decimal_places=1000)
    x = gis_models.DecimalField(max_digits=1000, decimal_places=1000)
    y = gis_models.DecimalField(max_digits=1000, decimal_places=1000)
    the_geom = gis_models.MultiPolygonField(srid=-1)
    objects = gis_models.GeoManager()
    class Meta:
        db_table = u'waterbalance_shape'
