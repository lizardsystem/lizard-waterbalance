import django.forms as forms

from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location

from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import WaterbalanceTimeserie


class PumpingStationForm(forms.ModelForm):
    """Implements the Admin form of a PumpingStation

    This form only hides some of the default model fields. These hidden model
    fields might come in handy sometime, but for now they only clutter the
    model interface.

    """
    class Meta:
        model = PumpingStation
        exclude = ['fractions']


class WaterbalanceTimeserieForm(forms.ModelForm):
    """Implements the Admin form of a WaterbalanceTimeserie.

    This form only hides some of the default model fields. These hidden model
    fields might come in handy sometime, but for now they only clutter the
    model interface.

    """
    class Meta:
        model = WaterbalanceTimeserie
        exclude = ['label', 'chloride', 'phosphate', 'nitrate', 'sulfate']

