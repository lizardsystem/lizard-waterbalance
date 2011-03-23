import datetime
import logging

from django.core.management.base import BaseCommand
from lizard_waterbalance.compute import WaterbalanceComputer2
from lizard_waterbalance.models import IncompleteData
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import Parameter
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceTimeserie

# from lizard_waterbalance.models import WaterbalanceTimeserie
# from lizard_waterbalance.models import Parameter


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Jacks test command."

    def handle(self, *args, **options):
        logger.info('Jacktest')

        # configuration_slug = "aetsveldsche_polder_oost_-_test"
        start = datetime.datetime(2005, 1, 1)
        end = datetime.datetime(2011, 1, 1)

        # configuration = WaterbalanceConf.objects.get(
        #     slug=configuration_slug)

        done_list = []

        # Testing: update with dummy data
        # for c in WaterbalanceConf.objects.all():
        #     if c.precipitation is None:
        #         c.precipitation = WaterbalanceTimeserie.objects.get(pk=21)
        #     if c.evaporation is None:
        #         c.evaporation = WaterbalanceTimeserie.objects.get(pk=22)
        #     if c.open_water is None:
        #         c.open_water = OpenWater.objects.get(pk=2)
        #     c.save()

        # Loop all configurations, try to calculate sluice errors.
        for configuration in WaterbalanceConf.objects.all():
            logger.info('Processing %s...' % configuration)
            waterbalance_computer = WaterbalanceComputer2(configuration)

            try:
                waterbalance_computer.get_sluice_error_timeseries(
                    start, end,
                    timestep=WaterbalanceTimeserie.TIMESTEP_MONTH)
                done_list.append(configuration)
            except IncompleteData:
                logger.info('Skipped because of incomplete data')

            # print wb_ts.get_timeseries().timeseries_events.filter(
            #     time__gte=start, time__lte=end)

        logger.info('*****************')
        logger.info('Succesfully done:')
        for d in done_list:
            logger.info(d)
