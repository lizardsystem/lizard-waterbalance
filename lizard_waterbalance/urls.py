# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
# from django.core.urlresolvers import reverse


admin.autodiscover()

crumbs_waterbalance = [
    {'name': 'home', 'url': '/', 'title': 'hoofdpagina'},
    # ^^^ Pretty hardcoded and Dutch.
    ]

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    # Waterbalance screens.
    (r'^$',
     'lizard_waterbalance.views.waterbalance_start',
     {'crumbs_prepend': list(crumbs_waterbalance),
      },
     'waterbalance_start'),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)/$',
     'lizard_waterbalance.views.waterbalance_area_summary',
     {'crumbs_prepend': list(crumbs_waterbalance),
      },
     'waterbalance_area_summary',
     ),

    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/$',
     'lizard_waterbalance.views.waterbalance_area_edit',
     {'crumbs_prepend': list(crumbs_waterbalance),
      },
     'waterbalance_area_edit',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/conf/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_conf',
     {},
     'waterbalance_area_edit_sub_conf',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/openwater/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_openwater',
     {},
     'waterbalance_area_edit_sub_openwater',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/buckets/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_buckets',
     {},
     'waterbalance_area_edit_sub_buckets',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/out/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_out',
     {},
     'waterbalance_area_edit_sub_out',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/in/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_in',
     {},
     'waterbalance_area_edit_sub_in',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/in/(?P<pump_id>[^/]+)/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_in_single',
     {},
     'waterbalance_area_edit_sub_in_single',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/labels/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub_labels',
     {},
     'waterbalance_area_edit_sub_labels',
     ),
    (r'^summary/(?P<area_slug>[^/]+)/scenario/(?P<scenario_slug>[^/]+)'
     '/edit/7/$',
     'lizard_waterbalance.views.waterbalance_area_edit_sub7',
     {},
     'waterbalance_area_edit_sub7',
     ),
    # TODO: 1..6 as parameter??

    (r'^summary/(?P<area_slug>.*)/recalculate_graph_data/$',
     'lizard_waterbalance.views.recalculate_graph_data',
     {},
     "waterbalance_graph_recalculate_data"),
    (r'^summary/(?P<area_slug>.*)/scenario/(?P<scenario_slug>.*)'
     '/recalculate_graph_data/$',
     'lizard_waterbalance.views.recalculate_graph_data',
     {},
     "waterbalance_graph_recalculate_data"),
    (r'^summary/(?P<area_slug>.*)/scenario/(?P<scenario_slug>.*)'
     '/graph/(?P<graph_type>.*)/$',
     'lizard_waterbalance.views.waterbalance_area_graphs',
     {},
     'waterbalance_area_graph'),
    (r'^graphselect/$',
     'lizard_waterbalance.views.graph_select',
     {},
     "waterbalance_graph_select"),
    (r'^area_search/',
     'lizard_waterbalance.views.waterbalance_shapefile_search',
     {},
     "waterbalance_area_search"),
    (r'^search_fews_lkeys/',
     'lizard_waterbalance.views.search_fews_lkeys',
     {},
     "waterbalance_search_fews_lkeys"),
    # Viewer
    (r'^viewer/$',
     'lizard_waterbalance.viewer.waterbalance_viewer',
     {},
     "waterbalance_viewer"),
    )

if settings.DEBUG:
    # Add this also to the projects that use this application
    urlpatterns += patterns('',
        (r'', include('staticfiles.urls')),
    )
