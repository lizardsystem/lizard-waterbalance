import django.forms as forms
from django.utils.translation import ugettext as _

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Location

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
        exclude = ['pkey', 'fkey', 'lkey']

    choices = [(parameter.pkey, "%s, pkey %d" % (parameter.name, parameter.pkey))
               for parameter in Parameter.objects.all().order_by("name")]
    name_parameter = forms.ChoiceField(label=_("Parameter"),
                                       help_text=_("naam, pkey van de parameter in FEWS unblobbed"),
                                       choices=choices)

    choices = [(filter.id, "%s, fkey %d" % (filter.name, filter.id))
               for filter in Filter.objects.all().order_by("name")]
    name_filter = forms.ChoiceField(label=_("Filter"),
                                    help_text=_("naam, fkey van de filter in FEWS unblobbed"),
                                    choices=choices)

    choices = []
    name_location = forms.CharField(label=_("Locatie"),
                                    help_text=_("naam, lkey van de locatie in FEWS unblobbed"),
                                    widget=forms.Select)

    def __init__(self, *args, **kwargs):
        super(TimeseriesFewsForm, self).__init__(*args, **kwargs)
        print self.fields['name_parameter'].widget.attrs


    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(TimeseriesFewsForm, self).save(commit=False)
        m.pkey = int(self.cleaned_data['name_parameter'])
        m.fkey = int(self.cleaned_data['name_filter'])
        m.lkey = int(self.cleaned_data['name_location'])
        if commit:
            m.save()
        return m


class WaterbalanceTimeserieForm(forms.ModelForm):
    """Implements the Admin form of a WaterbalanceTimeserie.

    This form only hides some of the default model fields. These hidden model
    fields might come in handy sometime, but for now they only clutter the
    model interface.

    """
    class Meta:
        model = WaterbalanceTimeserie
        exclude = ['label', 'chloride', 'phosphate', 'nitrate', 'sulfate']
