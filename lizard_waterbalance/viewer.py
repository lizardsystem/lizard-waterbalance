# Views for lizard viewer
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

from lizard_waterbalance.views import GRAPH_TYPES
from lizard_waterbalance.views import IMPLEMENTED_GRAPH_TYPES


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

    # Collect implemented graph types for displaying.
    graph_types_dict = dict(GRAPH_TYPES)
    graph_types = [(gt, graph_types_dict[gt])
                   for gt in IMPLEMENTED_GRAPH_TYPES]

    return render_to_response(
        template,
        {'javascript_hover_handler': 'popup_hover_handler',
         'javascript_click_handler': javascript_click_handler,
         'graph_types': graph_types,
         'crumbs': crumbs},
        context_instance=RequestContext(request))
