from django.contrib import admin

# from lizard_fewsunblobbed.models import Location
# from lizard_fewsunblobbed.models import Timeserie

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

class TimeseriesFewsAdmin(admin.ModelAdmin):
    raw_id_fields = ("fews_location",)
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "fews_location":
    #         timeseries = Timeserie.objects.filter(parameterkey=110, filterkey=8)
    #         kwargs["queryset"] = Location.objects.filter(timeserie__in=timeseries)
    #     return super(TimeseriesFewsAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Bucket)
admin.site.register(Concentration)
admin.site.register(OpenWater)
admin.site.register(PumpLine)
admin.site.register(PumpingStation)
admin.site.register(Timeseries)
admin.site.register(TimeseriesEvent)
admin.site.register(TimeseriesFews, TimeseriesFewsAdmin)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceLabel)
admin.site.register(WaterbalanceTimeserie)
