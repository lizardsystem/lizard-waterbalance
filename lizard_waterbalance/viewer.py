# Views for lizard viewer
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

from lizard_waterbalance.views import GRAPH_TYPES
from lizard_waterbalance.views import IMPLEMENTED_GRAPH_TYPES
from lizard_waterbalance.layers import AdapterWaterbalance


GRAPH_PARAMETERS = [
    ('fosfaat', 'Fosfaat'),
    ('inlaatwater', 'Percentage inlaatwater'),
    ('sluitfout', 'Sluitfout'),
    ('verblijftijd', 'Verblijftijd water')]


class ViewIcons(object):
    """Shortcut to get icon urls for different geo types"""

    def __init__(self):
        self.adapters = dict([
                (parameter_type,
                 AdapterWaterbalance(
                        workspace_item=None,
                        layer_arguments={'parameter': parameter_type}))
                for parameter_type, parameter_name in GRAPH_PARAMETERS])

    def url(self, graph_type, identifier=None,
            start_date=None, end_date=None):
        return self.adapters[graph_type].symbol_url(
            identifier=identifier,
            start_date=start_date,
            end_date=end_date)


def waterbalance_viewer(
    request,
    javascript_click_handler='popup_click_handler',
    template="lizard_waterbalance/viewer.html",
    crumbs_prepend=None):

    if crumbs_prepend is not None:
        crumbs = list(crumbs_prepend)
    else:
        crumbs = [{'name': 'home', 'url': '/'}]
    crumbs.append({'name': 'waterbalance',
                   'url': reverse('waterbalance_viewer')})

    icons = ViewIcons()

    # Collect implemented graph types for displaying.
    # graph_types_dict = dict(GRAPH_TYPES)
    # graph_types = [(gt, graph_types_dict[gt])
    #                for gt in IMPLEMENTED_GRAPH_TYPES]
    graph_types = [
        (parameter_type, parameter_name, icons.url(parameter_type))
        for parameter_type, parameter_name in GRAPH_PARAMETERS]

    return render_to_response(
        template,
        {'javascript_hover_handler': 'popup_hover_handler',
         'javascript_click_handler': javascript_click_handler,
         'graph_types': graph_types,
         'crumbs': crumbs},
        context_instance=RequestContext(request))
