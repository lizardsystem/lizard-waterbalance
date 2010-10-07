# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db import models

from lizard_fewsunblobbed.models import Timeserie


# Create your models here.

class Polder(models.Model):
    """Represents the area of which we want to know the waterbalance."""

    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=80)
    slug = models.SlugField(help_text=u"Name used for URL.")

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
    net_precipitation = models.ForeignKey(Timeserie)
    evaporation = models.ForeignKey(Timeserie)
    flow_off = models.ForeignKey(Timeserie)
    drainage = models.ForeignKey(Timeserie)
    indraft = models.ForeignKey(Timeserie)
    seepage = models.ForeignKey(Timeserie)


class StackedBucket(Bucket):
    """Represents a *gestapeld bakje*."""
    pass


class OpenWaterBucket(Bucket):
    """Represents an *open water(bakje)*."""
    pass
