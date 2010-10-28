# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# $Id$

from django.db import models

from lizard_fewsunblobbed.models import Timeserie


# Create your models here.

class Label(models.Model):
    """Specifies the name of a parameter group.

    Instance variables:
    * name -- name of the group of parameters to which the parameter belongs
    * color -- hex code of the color used for a value of the parameter group

    """
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=64)


class Bucket(models.Model):
    """Represents a *bakje*.

    Instance variables:
    * name -- name to show to the user
    * surface -- surface in [ha]
    * is_collapsed -- holds if and only if the bucket is a single bucket
    * precipitation -- time series for *neerslag*
    * evaporation -- time series for *verdamping*
    * flow_off -- time series for *afstroming*
    * drainage -- time series for *drainage*
    * indraft  -- time series for *intrek*
    * seepage -- time series for *kwel*
    * open_water -- link to the open_water to which this bucket belongs

    """
    name = models.CharField(max_length=64)
    surface = models.IntegerField()

    # A Bucket has links to several Timeseries or in Django terms, a Bucket has
    # multiple foreign keys to a Timeseries. For each foreign key from a Bucket
    # to a Timeseries, Django automatically creates a reverse relation back to
    # a Bucket, usually called 'bucket_set'. But this would mean that a
    # Timeseries ends up with multiple attributes with the same name, which is
    # not allowed. Therefore we tell Django what name to use for the relation
    # to the Bucket through the use of the named argument related_name.
    precipitation = models.ForeignKey(Timeserie,
                                      related_name='bucket_net_precipitation')
    evaporation = models.ForeignKey(Timeserie,
                                    related_name='bucket_evaporation')
    flow_off = models.ForeignKey(Timeserie, related_name='bucket_flow_off')
    drainage = models.ForeignKey(Timeserie, related_name='bucket_drainage')
    indraft = models.ForeignKey(Timeserie, related_name='bucket_indraft')
    seepage = models.ForeignKey(Timeserie, related_name='bucket_seepage')

    # We now couple a bucket to the open water although from a semantic point
    # of view, an open water should reference the buckets. However, this is the
    # usual way to implement a one-to-many relationship.
    open_water = models.ForeignKey("Bucket",
                                   null=True,
                                   blank=True,
                                   related_name='buckets')


class OpenWater(Bucket):
    """Represents an *open water(bakje)*.

    Instance variables:
    * minimum_height -- minimum allowed water height in [m]
    * maximum_height -- maximum allowed water height in [m]
    * intake -- time series for *intake*
    * pumps -- links to time series for discharge from area (often polder)
    * sluice_error -- time series for model errors

    To get to the buckets that have access to the current open water, use the
    implicit attribute 'buckets' which is a Manager for these buckets.

    According to Bastiaan, intake consists of two parts: doorspoeling and
    peilhandhaving. What should we do with this?

    """
    minimum_height = models.IntegerField()
    maximum_height = models.IntegerField()
    intake = models.ForeignKey(Timeserie, related_name='openwater_intake')
    pumps = models.ManyToManyField(Timeserie, related_name='openwater_pumps')
    sluice_error = models.ForeignKey(Timeserie,
                                     related_name='openwater_sluice_error')


class WaterbalanceArea(models.Model):
    """Represents the area of which we want to know the waterbalance.

    Instance variables:
    * name -- name to show to the user
    * slug -- unique name to construct the URL
    * description -- general description
    * open_water -- link to the open water

    """
    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=80)
    slug = models.SlugField(help_text=u"Name used for URL.")
    description = models.TextField(null=True,
                                   blank=True,
                                   help_text="You can use markdown")

    open_water = models.ForeignKey(OpenWater, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('krw_waternet.waterbalance', (), {'area': str(self.slug)})
