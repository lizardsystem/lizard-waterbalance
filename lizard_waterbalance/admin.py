from django.contrib import admin

from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceLabel


admin.site.register(WaterbalanceTimeserie)
admin.site.register(Bucket)
admin.site.register(OpenWater)
admin.site.register(PumpingStation)
admin.site.register(PumpLine)
admin.site.register(WaterbalanceArea)
admin.site.register(WaterbalanceLabel)
