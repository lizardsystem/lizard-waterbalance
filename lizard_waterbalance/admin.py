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
from lizard_waterbalance.models import SobekBucket


class BucketInLine(admin.TabularInline):
    model = Bucket

class SobekBucketInLine(admin.TabularInline):
    model = SobekBucket

class BucketAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'surface_type')
    list_display = ('name', 'open_water', 'surface_type', 'surface', 'crop_evaporation_factor', 'min_crop_evaporation_factor',
                     'upper_bucket_info', 'lower_bucket_info')
    search_fields = ['name', 'open_water', ]

class OpenWaterAdmin(admin.ModelAdmin):
    fieldsets = (
    (None, {
        'fields': ('name', 'surface', 'bottom_height', 'init_water_level', 'precipitation', 'evaporation', 'seepage',
                   'infiltration', 'sewer' )
    }),
        ('Waterpeil grenzen', {
        'description': 'Instellingen voor mininumum en maximumpeil, waarbinnen het peil gehouden moet worden. Er zijn twee opties: \
        (1) een vaste tijdreeks met minimum en maximum waarden of \
        (2) een constante afwijking t.o.v. het gemeten peil',
        'fields': ('use_min_max_level_relative_to_meas', ('waterlevel_measurement', 'min_level_relative_to_measurement',
                   'max_level_relative_to_measurement'), ('minimum_level', 'maximum_level'))
    }),
        ('Nutricalc', {
        'classes': ('collapse',),
        'fields': ('nutricalc_min', 'nutricalc_incr')
    }))


    list_display = ('name', 'surface',
                    'bottom_height', 'init_water_level', 'linked_with_configuration')
    search_fields = ['name', ]

    inlines = [
        BucketInLine,
        SobekBucketInLine
        ]


class SobekBucketAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'surface_type')
    list_display = ('name', 'open_water', 'surface_type')
    search_fields = ['name', 'open_water' ]


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

    # The following code is not allowed for non-editable fields, which is
    # explained in http://code.djangoproject.com/ticket/7280. Furthermore, the
    # ticket states that
    #
    #  "The slug field should not be editable by a user but rather is updated
    #   in the save() method of the model everytime the name of the menu
    #   changes."
    #
    # so we implemented a save() method for a Parameter.
    # prepopulated_fields = {'slug': ('name',)}


class ConcentrationInLine(admin.TabularInline):
    model = Concentration


class WaterbalanceConfAdmin(admin.ModelAdmin):
    list_filter = ('waterbalance_scenario', 'waterbalance_area',  )
    list_display = ('waterbalance_area', 'waterbalance_scenario',
                    'description')
    search_fields = ['waterbalance_scenario', 'waterbalance_area' ]
    filter_vertical = ['references']

    inlines = [
        ConcentrationInLine,
        ]


class TimeseriesEventInline(admin.TabularInline):
    model = TimeseriesEvent


def delete_timeseries_no_confirm(modeladmin, request, queryset):
    queryset.delete()
delete_timeseries_no_confirm.short_description = "verwijder geselecteerde tijdreeksen zonder goedkeuring"



class TimeseriesAdmin(admin.ModelAdmin):
    inlines = [
        TimeseriesEventInline,
        ]
    actions = [delete_timeseries_no_confirm]
    list_display = ('name', 'waterbalance_timeserie_info' )



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
                     'configuration', 'timestep', 'linked_with_info')
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
#admin.site.register(SobekBucket, SobekBucketAdmin)
#admin.site.register(Concentration)
admin.site.register(OpenWater, OpenWaterAdmin)
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

