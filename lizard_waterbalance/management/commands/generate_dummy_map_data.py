

from datetime import datetime
from os.path import join
import csv
import random

from django.core.management.base import BaseCommand

from lizard_waterbalance.compute import WaterbalanceComputer2
from lizard_waterbalance.models import WaterbalanceConf, WaterbalanceScenario, WaterbalanceArea, WaterbalanceTimeserie, Timeseries, TimeseriesEvent, Parameter



scenario, new = WaterbalanceScenario.objects.get_or_create(name='dummy')
parameter, new = Parameter.objects.get_or_create(name='dummy_month')


for area in WaterbalanceArea.objects.all():
    conf, new = WaterbalanceConf.objects.get_or_create(waterbalance_scenario=scenario, waterbalance_area=area)
    conf.slug = ("%s-%s"%(area.name[0:25], scenario.name)).replace(" ","_").lower()

    wb_timeseries, new = conf.results.get_or_create( name="%s-%s"%(conf.slug[0:40],parameter.name),
                                                parameter = parameter)
    if wb_timeseries.local_timeseries:
        ts = wb_timeseries.local_timeseries
    else:
        ts, new = Timeseries.objects.get_or_create(name = wb_timeseries.name)
        wb_timeseries.local_timeseries = ts

    ts.save()
    conf.save()
    scenario.save()
    wb_timeseries.save()
    parameter.save()

    ts.timeseries_events.all().delete()

    rand_value = random.randrange(3,10)
    for year in range(2005, 2010):
        for month in range(1,12):
           ts.timeseries_events.create(time=datetime(year,month,1), value=random.randrange(rand_value,10*rand_value))
