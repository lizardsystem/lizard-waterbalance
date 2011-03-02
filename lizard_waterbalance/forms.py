import django.forms as forms
from django.utils.translation import ugettext as _

from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location
from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Timeserie

from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import TimeseriesFews
from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_waterbalance.views import create_location_label


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

    name_parameter = forms.ChoiceField(label=_("Parameter"),
                                       help_text=_("naam, pkey van de parameter in FEWS unblobbed"),
                                       choices=[])

    name_filter = forms.ChoiceField(label=_("Filter"),
                                    help_text=_("naam, fkey van de filter in FEWS unblobbed"),
                                    choices=[])

    choices = []
    name_location = forms.CharField(label=_("Locatie"),
                                    help_text=_("naam, lkey van de locatie in FEWS unblobbed"),
                                    widget=forms.Select)

    def __init__(self, *args, **kwargs):
        super(TimeseriesFewsForm, self).__init__(*args, **kwargs)

        choices =  [(parameter.pkey, "%s, pkey %d" % (parameter.name, parameter.pkey))
                    for parameter in Parameter.objects.all().order_by("name")]
        self.fields['name_parameter'].choices = choices
        if not self.instance is None and not self.instance.pkey is None:
            self.fields['name_parameter'].initial = self.instance.pkey
            pkey = Parameter.objects.get(pkey=self.instance.pkey)
        else:
            pkey = None

        choices = [(filter.id, "%s, fkey %d" % (filter.name, filter.id))
                   for filter in Filter.objects.all().order_by("name")]
        self.fields['name_filter'].choices = choices
        if not self.instance is None and not self.instance.fkey is None:
            self.fields['name_filter'].initial = self.instance.fkey
            fkey = Filter.objects.get(id=self.instance.fkey)
        else:
            fkey = None

        if not pkey is None and not fkey is None:
            timeseries = Timeserie.objects.filter(parameterkey=pkey.pkey, filterkey=fkey.id)
            timeseries = timeseries.distinct().order_by("locationkey")
            choices = [(ts.locationkey.lkey, create_location_label(ts.locationkey)) for ts in timeseries]
            print choices
            self.fields['name_location'].widget.choices = choices
            if not self.instance is None and not self.instance.lkey is None:
                self.fields['name_location'].initial = str(self.instance.lkey)


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
