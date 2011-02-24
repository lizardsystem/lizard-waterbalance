import django.forms as forms

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Parameter

from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import TimeseriesFews
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


class TimeseriesFewsForm(forms.ModelForm):

    class Meta:
        model = TimeseriesFews
    def __init__(self, *args, **kwargs):
        super(TimeseriesFewsForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['fews_parameter'].queryset = \
                Parameter.objects.all().order_by('name')
            self.fields['fews_filter'].queryset = \
                Filter.objects.all().order_by('name')


class WaterbalanceTimeserieForm(forms.ModelForm):
    """Implements the Admin form of a WaterbalanceTimeserie.

    This form only hides some of the default model fields. These hidden model
    fields might come in handy sometime, but for now they only clutter the
    model interface.

    """
    class Meta:
        model = WaterbalanceTimeserie
        exclude = ['label', 'chloride', 'phosphate', 'nitrate', 'sulfate']
