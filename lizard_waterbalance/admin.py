import logging

from django.contrib import admin
import django.forms as forms
from django.utils.translation import ugettext as _

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

logger = logging.getLogger(__name__)


class BucketInLine(admin.TabularInline):
    model = Bucket


class SobekBucketInLine(admin.TabularInline):
    model = SobekBucket


class BucketAdmin(admin.ModelAdmin):
    list_filter = ('open_water', 'surface_type')
    list_display = ('name', 'open_water', 'surface_type', 'surface', 'crop_evaporation_factor', 'min_crop_evaporation_factor',
                     'upper_bucket_info', 'lower_bucket_info')
    search_fields = ['name', 'open_water', ]


class OpenWaterAdminForm(forms.ModelForm):

    def clean(self):
        """Return the dictionary of cleaned data if and only if it is correct.

        This method checks whether the user has specified the required fields
        for level control. If that is the case, this method returns the
        dictionary of cleaned data, otherwise this method throws a
        forms.ValidationError.
        """
        message = None
        cleaned_data = self.cleaned_data
        if cleaned_data.get("use_min_max_level_relative_to_meas", False):
            if self._a_field_is_empty(["waterlevel_measurement"]):
                message = "Als het minimum en maximum peil ten opzichte van " \
                          "het gemeten peil gebruikt dienen te worden, dan " \
                          "moet het gemeten peil ook zijn ingevuld."
        else:
            if self._a_field_is_empty(["minimum_level", "maximum_level"]):
                message = "Als het minimum en maximum peil gebruikt dienen " \
                          "te worden, dan moeten deze ook zijn ingevuld."
        if not message is None:
            raise forms.ValidationError(_(message))
        return self.cleaned_data

    def _a_field_is_empty(self, field_names):
        """Return True if and only if a given field name is missing or None.

        """
        for field_name in field_names:
            if self.cleaned_data.get(field_name, None) is None:
                return True
        return False


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

    form = OpenWaterAdminForm



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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Order the time series in the select list of each PumpLine.

        This solution was found in the documentation of Django,
        http://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.formfield_for_foreignkey

        """
        if db_field.name == "timeserie":
            kwargs["queryset"] = \
                WaterbalanceTimeserie.objects.filter().order_by('name')
        return super(PumpLineInLine, self).formfield_for_foreignkey(db_field,
                                                                    request,
                                                                    **kwargs)


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
    # The user should not be able to add a new concentration, delete an
    # existing one or change the label of an existing one. First, the following
    # two assignments remove the extra fields that allow the user to enter a
    # new concentration and remove the check boxes that allow the user to
    # delete existings ones.
    extra = 0
    can_delete = False
    # Furthermore, we override the inline template in order to remove the
    # button that allows the user to add a new concentration.
    template = "admin/lizard_waterbalance/concentration/tabular.html"

    # Finally, we make the drop down box that contains the label read-only so
    # the user cannot modify it.
    def get_readonly_fields(self, request, obj=None):
        """Render the label field read-only.

        A user should not be able to edit the label of a concentration.
        """
        if obj: # editing an existing object
            return self.readonly_fields + ('label',)
        return self.readonly_fields

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
    list_filter = ('use_fews', 'parameter' )
    list_display = ( 'name', 'use_fews', 'parameter',
                     'fews_timeseries', 'local_timeseries',
                     'linked_with_info')
    search_fields = ['name',  ]

    form = WaterbalanceTimeserieForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Order the the contents of several select lists.

        This solution was found in the documentation of Django,
        http://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.formfield_for_foreignkey

        """
        if db_field.name == "parameter":
            kwargs["queryset"] = \
                Parameter.objects.filter().order_by('name')
        if db_field.name == "fews_timeseries":
            kwargs["queryset"] = \
                TimeseriesFews.objects.filter().order_by('name')
        if db_field.name == "local_timeseries":
            kwargs["queryset"] = \
                Timeseries.objects.filter().order_by('name')

        return super(WaterbalanceTimeserieAdmin, self).formfield_for_foreignkey(db_field,
                                                                     request,
                                                                     **kwargs)


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

