import django.forms as forms

from lizard_fewsunblobbed.models import Parameter
from lizard_fewsunblobbed.models import Filter
from lizard_fewsunblobbed.models import Location

from lizard_waterbalance.models import WaterbalanceTimeserie

GRAPH_TYPES = (
    ('waterbalans', u'Waterbalans'),
    ('waterpeil', u'Waterpeil'),
    ('waterpeil_met_sluitfout', u'Waterpeil met sluitfout'),
    ('cumulatief_debiet', u'Cumulatief debiet'),
    ('fracties_chloride', u'Fracties Chloride'),
    ('fracties_fosfaat', u'Fracties Fosfaat'),
    ('fosfaatbelasting', u'Fosfaatbelasting'),
)

class GraphtypeSelectionForm(forms.Form):
    """
    docstring for GraphtypeSelectionForm

    """
    graphs = forms.MultipleChoiceField(choices=GRAPH_TYPES,
                                       widget=forms.CheckboxSelectMultiple())


class WaterbalanceTimeserieForm(forms.ModelForm):
    """Implements the Admin form of a WaterbalanceTimeserie.

    This form only hides some of the default model fields. These nidden model
    fields might come in handy sometime, but for now they only clutter the
    model interface.

    """
    class Meta:
        model = WaterbalanceTimeserie
        exclude = ['label', 'chloride', 'phosphate', 'nitrate', 'sulfate']

