from django.contrib import admin

from lizard_waterbalance.forms import PumpingStationForm
from lizard_waterbalance.forms import TimeseriesFewsForm
from lizard_waterbalance.forms import WaterbalanceTimeserieForm

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import Concentration
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import Parameter
from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import TimeseriesEvent
from lizard_waterbalance.models import TimeseriesFews
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceScenario
from lizard_waterbalance.models import Label
from lizard_waterbalance.models import WaterbalanceTimeserie

class BucketAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'surface_type')
    list_display = ('name', 'open_water', 'surface_type', 'surface', 'crop_evaporation_factor', 'min_crop_evaporation_factor',
                     'upper_bucket_info', 'lower_bucket_info')
    search_fields = ['name', 'open_water', ]



 


class PumpLineAdmin(admin.ModelAdmin):
    list_filter = ('pumping_station', )
    list_display = ('name', 'pumping_station', )
    search_fields = ['name', 'pumping_station', ]


class PumpLineInLine(admin.TabularInline):
    model = PumpLine


class PumpingStationAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'into', 'computed_level_control' )
    list_display = ('name', 'open_water', 'into', 'label',
                    'computed_level_control', 'percentage', 'max_discharge')
    search_fields = ['name', 'open_water', ]

    inlines = [
        PumpLineInLine,
        ]
    form = PumpingStationForm
    
class ParameterAdmin(admin.ModelAdmin):
    list_filter = ('sourcetype', 'parameter')
    list_display = ('name', 'unit', 'slug', 'parameter',
                    'sourcetype')
    search_fields = ['name']
    
    prepopulated_fields = {'slug': ('name',)}


class ConcentrationInLine(admin.TabularInline):
    model = Concentration


class WaterbalanceConfAdmin(admin.ModelAdmin):
    list_filter = ('waterbalance_scenario', 'waterbalance_area',  )
    list_display = ('waterbalance_scenario', 'waterbalance_area',
                    'description')
    search_fields = ['waterbalance_scenario', 'waterbalance_area' ]
    
    inlines = [
        ConcentrationInLine,
        ]



class TimeseriesEventInline(admin.TabularInline):
    model = TimeseriesEvent


class TimeseriesAdmin(admin.ModelAdmin):
    inlines = [
        TimeseriesEventInline,
        ]


class TimeseriesFewsAdmin(admin.ModelAdmin):
    # raw_id_fields = ("fews_location",)
    form = TimeseriesFewsForm


class LabelAdmin(admin.ModelAdmin):
    list_filter = ('flow_type', )
    list_display = ( 'name', 'program_name', 'order',
                     'color', 'color_increment', 'flow_type')
    search_fields = ['name', ]

class WaterbalanceTimeserieAdmin(admin.ModelAdmin):
    list_filter = ('use_fews', 'parameter', 'configuration', 'timestep' )
    list_display = ( 'name', 'use_fews', 'parameter',
                     'fews_timeseries', 'local_timeseries',
                     'configuration', 'timestep')
    search_fields = ['name',  ]

    form = WaterbalanceTimeserieForm


class WaterbalanceAreaAdmin(admin.ModelAdmin):
    list_filter = ('public', )
    list_display = ( 'name', 'public', 'description', )
    search_fields = ['name', ]

class WaterbalanceScenarioAdmin(admin.ModelAdmin):
    list_filter = ('public', 'active' )
    list_display = ( 'name', 'order', 'active', 'public')
    search_fields = ['name', ]    
    
    


admin.site.register(Bucket, BucketAdmin)
#admin.site.register(Concentration)
admin.site.register(OpenWater)
admin.site.register(Parameter, ParameterAdmin)
#admin.site.register(PumpLine, PumpLineAdmin)
admin.site.register(PumpingStation, PumpingStationAdmin)
admin.site.register(Timeseries, TimeseriesAdmin)
#admin.site.register(TimeseriesEvent)
admin.site.register(TimeseriesFews, TimeseriesFewsAdmin)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceConf, WaterbalanceConfAdmin)
admin.site.register(WaterbalanceScenario, WaterbalanceScenarioAdmin)
admin.site.register(Label, LabelAdmin)
admin.site.register(WaterbalanceTimeserie, WaterbalanceTimeserieAdmin)

