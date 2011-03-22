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
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceScenario
from lizard_waterbalance.models import WaterbalanceLabel
from lizard_waterbalance.models import WaterbalanceTimeserie

class BucketAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'surface_type' )
    list_display = ('name', 'open_water', 'surface_type', 'surface',)
    search_fields = ['name', 'open_water', ]


class PumpLineAdmin(admin.ModelAdmin):
    list_filter = ('pumping_station', )
    list_display = ('name', 'pumping_station', )
    search_fields = ['name', 'pumping_station', ]


class PumpLineInLine(admin.TabularInline):
    model = PumpLine


class PumpingStationAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'into', 'computed_level_control' )
    list_display = ('name', 'open_water', 'into', 'computed_level_control', 'percentage', 'max_discharge')
    search_fields = ['name', 'open_water', ]
    
    inlines = [
        PumpLineInLine,
        ]
    form = PumpingStationForm

class WaterbalanceConfAdmin(admin.ModelAdmin):
    list_filter = ('waterbalance_scenario', 'waterbalance_area',  )
    list_display = ( 'slug', 'waterbalance_scenario', 'waterbalance_area', 'description')
    search_fields = ['waterbalance_scenario', 'waterbalance_area' ]

class TimeseriesEventInline(admin.TabularInline):
    model = TimeseriesEvent


class TimeseriesAdmin(admin.ModelAdmin):
    inlines = [
        TimeseriesEventInline,
        ]


class TimeseriesFewsAdmin(admin.ModelAdmin):
    # raw_id_fields = ("fews_location",)
    form = TimeseriesFewsForm
   

class WaterbalanceTimeserieAdmin(admin.ModelAdmin):
    list_filter = ('use_fews', 'parameter',  )
    list_display = ( 'name', 'use_fews', 'parameter', 'fews_timeseries', 'local_timeseries')
    search_fields = ['name',  ]
    
    form = WaterbalanceTimeserieForm
    
class WaterbalanceAreaAdmin(admin.ModelAdmin):
    list_filter = ('public', )
    list_display = ( 'name', 'public', 'description', )
    search_fields = ['name', ]


admin.site.register(Bucket, BucketAdmin)
admin.site.register(Concentration)
admin.site.register(OpenWater)
admin.site.register(PumpLine, PumpLineAdmin)
admin.site.register(PumpingStation, PumpingStationAdmin)
admin.site.register(Timeseries, TimeseriesAdmin)
admin.site.register(TimeseriesEvent)
admin.site.register(TimeseriesFews, TimeseriesFewsAdmin)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceConf, WaterbalanceConfAdmin)
admin.site.register(WaterbalanceScenario)
admin.site.register(WaterbalanceLabel)
admin.site.register(WaterbalanceTimeserie, WaterbalanceTimeserieAdmin)

