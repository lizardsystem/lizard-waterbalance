import datetime
import logging

from django.core.management.base import BaseCommand
from lizard_waterbalance.models import IncompleteData
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_wbcomputation.compute import WaterbalanceComputer2


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = ("Compute timeseries which are visible "
            "in the geographical environment.")

    def handle(self, *args, **options):
        logger.info('Start computing timeseries.')

        start_date_calc = datetime.datetime(1900, 1, 1)
        end_date_calc = (datetime.datetime.now() +
                         datetime.timedelta(days=31))

        done_list = []

        # Loop all configurations, try to calculate sluice errors.
        for configuration in WaterbalanceConf.objects.all():
            logger.info('Processing %s...' % configuration)
            waterbalance_computer = WaterbalanceComputer2(configuration)

            try:
                logger.info('Computing sluice errors...')
                waterbalance_computer.calc_and_store_sluice_error_timeseries(
                    start_date_calc, end_date_calc,
                    timestep=WaterbalanceTimeserie.TIMESTEP_MONTH)
                done_list.append(configuration)
            except IncompleteData:
                logger.info('Skipped because of incomplete data.')

        logger.info('*****************')
        logger.info('Succesfully done:')
        for d in done_list:
            logger.info(d)
