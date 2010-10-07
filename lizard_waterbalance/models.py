# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db import models

from lizard_fewsunblobbed.models import Timeserie


# Create your models here.

class Polder(models.Model):
    """Represents the area of which we want to know the waterbalance.

    Instance variables:
    * name -- name to show to the user
    * slug -- unique name to construct the URL
    * description -- general description
    """
    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=80)
    slug = models.SlugField(help_text=u"Name used for URL.")
    description = models.TextField(null=True,
                                   blank=True,
                                   help_text="You can use markdown")

    def __unicode__(self):
        return unicode(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('krw_waternet.waterbody', (), {'area': str(self.slug)})


class TimeserieWaterbalance(Timeserie):
    """Represents a time series of in or outgoing water.

    Instance variables:
    * name -- name to show to the user
    * is_outgoing -- holds for outgoing water
    """
    name = models.CharField(max_length=64)
    is_outgoing = models.BooleanField()


class Bucket(models.Model):
    """Represents a *bakje*.

    Instance variables:
    * name -- name to show to the user
    * surface -- surface in [ha]
    * precepitation -- time series for *neerslag*
    * evaporation -- time series for *verdamping*
    * flow_off -- time series for *afstroming*
    * drainage -- time series for *drainage*
    * indraft  -- time series for *intrek*
    * seepage -- time series for *kwel*

    """
    name = models.CharField(max_length=64)
    surface = models.IntegerField()

    # To have links to multiple time series, we need to use the named argument
    # 'related_name'. But Django automatically creates a reverse relation from
    # a Bucket to a Timeseries, usually called 'bucket_set'. As a Bucket has
    # multiple foreign keys to a Timeseries, a Timeseries would end up with
    # multiple attributes with the same name. Therefore we tell Django what
    # name to use for the relation to the Bucket.
    net_precipitation =  \
        models.ForeignKey(Timeserie, related_name='bucket_net_precipitation')
    evaporation = \
        models.ForeignKey(Timeserie, related_name='bucket_evaporation')
    flow_off = models.ForeignKey(Timeserie, related_name='bucket_flow_off')
    drainage = models.ForeignKey(Timeserie, related_name='bucket_drainage')
    indraft = models.ForeignKey(Timeserie, related_name='bucket_indraft')
    seepage = models.ForeignKey(Timeserie, related_name='bucket_seepage')


class StackedBucket(Bucket):
    """Represents a *gestapeld bakje*."""
    pass


class OpenWaterBucket(Bucket):
    """Represents an *open water(bakje)*."""
    pass
