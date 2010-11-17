from django.contrib import admin

from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceLabel


class OpenWaterAdmin(admin.ModelAdmin):
    exclude = ('indraft',
               'drainage',
               'flow_off',
               'computed_flow_off',
               'open_water')


admin.site.register(WaterbalanceTimeserie)
admin.site.register(Bucket)
admin.site.register(OpenWater, OpenWaterAdmin)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceLabel)
