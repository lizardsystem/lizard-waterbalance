# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    # Waterbalance screens.
    (r'^$',
     'lizard_waterbalance.views.waterbalance_start',
     {},
     'waterbalance_start'),
     (r'^summary/(?P<area>[^/]+)/$',
     'lizard_waterbalance.views.waterbalance_area_summary',
     {},
     'waterbalance_area_summary',
     ),
    (r'^summary/(?P<area>.*)/recalculate_graph_data/$',
     'lizard_waterbalance.views.recalculate_graph_data',
     {},
     "waterbalance_graph_recalculate_data"),
    (r'^summary/(?P<area>.*)/(?P<graph_type>.*)/$',
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
    )


if settings.DEBUG:
    # Add this also to the projects that use this application
    urlpatterns += patterns('',
        (r'', include('staticfiles.urls')),
    )
