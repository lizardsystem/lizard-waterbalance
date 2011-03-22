# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

import datetime

from django.test import TestCase


from lizard_waterbalance.models import Parameter
# from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceTimeserie


class TestModels(TestCase):

    def test_waterbalance_timeserie_create(self):
        """
        Creates local waterbalance timeserie.
        """
        parameter = Parameter(name='test parameter', unit='nvt')
        parameter.save()
        c = None  # WaterbalanceConf.objects.all()[0]
        timestep = WaterbalanceTimeserie.TIMESTEP_DAY
        ts = {
            datetime.datetime(2011, 1, 1): 1.414,
            datetime.datetime(2011, 2, 1): 2.25,
            datetime.datetime(2011, 3, 1): 2.71,
            }
        wb_ts = WaterbalanceTimeserie.create(
            name='jacktest', parameter=parameter,
            timeseries=ts, configuration=c, timestep=timestep)
        ts = wb_ts.get_timeseries()
        events = ts.timeseries_events.all()
        self.assertEquals(events[0].time, datetime.datetime(2011, 1, 1))
        self.assertEquals(events[0].value, 1.414)  # Does it work? Float..
        self.assertEquals(events[1].time, datetime.datetime(2011, 2, 1))
        self.assertEquals(events[1].value, 2.25)  # Does it work? Float..
        self.assertEquals(events[2].time, datetime.datetime(2011, 3, 1))
        self.assertEquals(events[2].value, 2.71)  # Does it work? Float..

