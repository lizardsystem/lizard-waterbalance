from django.contrib import admin

from lizard_waterbalance.forms import PumpingStationForm
from lizard_waterbalance.forms import TimeseriesFewsForm
from lizard_waterbalance.forms import WaterbalanceTimeserieForm

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import Concentration
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import TimeseriesEvent
from lizard_waterbalance.models import TimeseriesFews
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceLabel
from lizard_waterbalance.models import WaterbalanceTimeserie


class PumpLineInLine(admin.TabularInline):
    model = PumpLine


class PumpingStationAdmin(admin.ModelAdmin):
    inlines = [
        PumpLineInLine,
        ]
    form = PumpingStationForm


class TimeseriesEventInline(admin.TabularInline):
    model = TimeseriesEvent


class TimeseriesAdmin(admin.ModelAdmin):
    inlines = [
        TimeseriesEventInline,
        ]


class TimeseriesFewsAdmin(admin.ModelAdmin):
    raw_id_fields = ("fews_location",)
    form = TimeseriesFewsForm


class WaterbalanceTimeserieAdmin(admin.ModelAdmin):
    form = WaterbalanceTimeserieForm


admin.site.register(Bucket)
admin.site.register(Concentration)
admin.site.register(OpenWater)
admin.site.register(PumpLine)
admin.site.register(PumpingStation, PumpingStationAdmin)
admin.site.register(Timeseries, TimeseriesAdmin)
admin.site.register(TimeseriesEvent)
admin.site.register(TimeseriesFews, TimeseriesFewsAdmin)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceLabel)
admin.site.register(WaterbalanceTimeserie, WaterbalanceTimeserieAdmin)

