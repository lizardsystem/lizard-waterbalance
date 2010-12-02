from django.contrib import admin

from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceLabel


class OpenWaterAdmin(admin.ModelAdmin):
    exclude = (
        'computed_flow_off',
        'crop_evaporation_factor',
        'drainage',
        'drainage_fraction',
        'equi_water_level',
        'flow_off',
        'indraft',
        'infiltration_fraction',
        'init_water_level',
        'max_water_level',
        'min_crop_evaporation_factor',
        'min_water_level',
        'open_water',
        'porosity',
        'surface_type',
        'upper_crop_evaporation_factor',
        'upper_min_crop_evaporation_factor',
        'upper_porosity'
        )


admin.site.register(WaterbalanceTimeserie)
admin.site.register(Bucket)
admin.site.register(OpenWater, OpenWaterAdmin)
admin.site.register(PumpingStation)
admin.site.register(PumpLine)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceLabel)
