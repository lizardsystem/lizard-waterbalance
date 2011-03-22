import datetime
import logging

from django.core.management.base import BaseCommand
from lizard_waterbalance.compute import WaterbalanceComputer2
from lizard_waterbalance.models import WaterbalanceConf

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Jacks test command."

    def handle(self, *args, **options):
        logger.info('test info')

        configuration_slug = "aetsveldsche_polder_oost_-_test"
        start = datetime.datetime(1900, 1, 1)
        end = datetime.datetime(2011, 1, 1)


        configuration = WaterbalanceConf.objects.get(
            slug=configuration_slug)

        waterbalance_computer = WaterbalanceComputer2(configuration)

        # waterbalance_computer.compute(start, end)
        ts = waterbalance_computer.get_sluice_error_timeseries(start, end)
        # print dir(ts)
        print [e for e in ts.events()]  # per dag
        # print [e for e in ts.monthly_events()]
        # print [e for e in ts.raw_events()]  # per dag
