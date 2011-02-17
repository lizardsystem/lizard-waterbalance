from django import forms

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
	graphs = forms.MultipleChoiceField(choices=GRAPH_TYPES, widget=forms.CheckboxSelectMultiple())
	
