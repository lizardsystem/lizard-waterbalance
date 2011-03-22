import datetime
import logging

from django.core.management.base import BaseCommand
from lizard_waterbalance.compute import WaterbalanceComputer2
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

        configuration_slug = "aetsveldsche_polder_oost_-_test"
        start = datetime.datetime(2010, 1, 1)
        end = datetime.datetime(2011, 1, 1)

        configuration = WaterbalanceConf.objects.get(
            slug=configuration_slug)
        parameter, created = Parameter.objects.get_or_create(
            name='sluitfout', unit='m')

        waterbalance_computer = WaterbalanceComputer2(configuration)

        wb_ts = waterbalance_computer.get_sluice_error_timeseries(
            start, end,
            timestep=WaterbalanceTimeserie.TIMESTEP_DAY,
            force_recalculate=False)

        print wb_ts.get_timeseries().timeseries_events.filter(
            time__gte=start, time__lte=end)
