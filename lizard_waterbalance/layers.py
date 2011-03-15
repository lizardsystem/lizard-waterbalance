import logging
import mapnik
from django.conf import settings
from django.contrib.gis.geos import Point

from lizard_map.adapter import Graph
from lizard_map.coordinates import GOOGLE
from lizard_map.coordinates import google_to_rd
from lizard_map.coordinates import RD
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_waterbalance.models import WaterbalanceShape

# testing
from lizard_waterbalance.views import waterbalance_area_graph

logger = logging.getLogger(__name__)


class AdapterWaterbalance(WorkspaceItemAdapter):
    """Adapter for module LizardWaterbalance.

    Registered as adapter_waterbalance.

    Uses default database table "waterbalance_shape" as geo database.
    """

    def __init__(self, *args, **kwargs):
        super(AdapterWaterbalance, self).__init__(*args, **kwargs)
        self.shape_tablename = 'waterbalance_shape'
        # See views.IMPLEMENTED_GRAPH_TYPES
        self.graph_type = self.layer_arguments['parameter']

    def _mapnik_style(self):
        """
        Temp function to return a default mapnik style
        """
        def mapnik_rule(r, g, b, mapnik_filter=None):
            """
            Makes mapnik rule for looks. For lines and polygons.

            From lizard_map.models.
            """
            rule = mapnik.Rule()
            if mapnik_filter is not None:
                rule.filter = mapnik.Filter(mapnik_filter)
            mapnik_color = mapnik.Color(r, g, b)

            symb_line = mapnik.LineSymbolizer(mapnik_color, 0)
            rule.symbols.append(symb_line)

            symb_poly = mapnik.PolygonSymbolizer(mapnik_color)
            symb_poly.fill_opacity = 1
            rule.symbols.append(symb_poly)
            return rule

        mapnik_style = mapnik.Style()
        rule = mapnik_rule(255, 0 ,0)
        mapnik_style.rules.append(rule)
        for gid in range(100):
            rule = mapnik_rule(0, 10 * gid ,0, '[gid] = %d' % gid)
            mapnik_style.rules.append(rule)
        # rule = mapnik_rule(0, 255, 0, '[value] <= 75')
        # mapnik_style.rules.append(rule)
        # rule = mapnik_rule(255, 0, 0, '[value] > 75')
        # mapnik_style.rules.append(rule)
        return mapnik_style

    def layer(self, layer_ids=None, request=None):
        """Return layer and styles for a parameter.
        """
        layers = []
        styles = {}

        table_view = ('(select the_geom, gid from %s) '
                      'result_view' % (
                self.shape_tablename))
        # table_view = ('(select the_geom, gid, value from %s '
        #               'inner join lizard_waterbalance_timeseries '
        #               #'as timeseries '
        #               'on waterbalance_shape.gafnaam = lizard_waterbalance_timeseries.name '
        #               'inner join lizard_waterbalance_timeseriesevent '
        #               #'as timeseriesevent '
        #               'on lizard_waterbalance_timeseries.id = lizard_waterbalance_timeseriesevent.timeseries_id '
        #               'where lizard_waterbalance_timeseriesevent.time = \'2011-03-01\') '
        #               'result_view' % (
        #         self.shape_tablename))
        mapnik_style = self._mapnik_style()

        lyr = mapnik.Layer('Geometry from PostGIS')
        lyr.srs = RD  #GOOGLE
        BUFFERED_TABLE = table_view
        db_settings = settings.DATABASES['default']
        lyr.datasource = mapnik.PostGIS(
            host=db_settings['HOST'],
            user=db_settings['USER'],
            password=db_settings['PASSWORD'],
            dbname=db_settings['NAME'],
            table=str(BUFFERED_TABLE))
        style_name = 'waterbalance_style'
        lyr.styles.append(style_name)

        layers.append(lyr)
        styles[style_name] = mapnik_style

        return layers, styles

    def search(self, x, y, radius=None):
        rd_x, rd_y = google_to_rd(x, y)
        results = [{
                'distance': 0,
                'name': wb_shape.gafnaam,
                'shortname': wb_shape.gafnaam,
                'workspace_item': self.workspace_item,
                'identifier': {},
                'object': wb_shape}
                   for wb_shape in WaterbalanceShape.objects.filter(
                the_geom__contains=Point(rd_x, rd_y))]
        return results

    def symbol_url(self, identifier=None, start_date=None,
                   end_date=None, icon_style=None):
        """
        Returns symbol.
        """
        icon_style = {'icon': 'polygon.png',
                      'mask': ('mask.png', ),
                      'color': (0, 1, 0, 0)}

        return super(AdapterWaterbalance, self).symbol_url(
            identifier=identifier,
            start_date=start_date,
            end_date=end_date,
            icon_style=icon_style)

    def location(self, parameter=None, layout=None):
        result = []
        return result

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        return super(AdapterWaterbalance, self).html_default(
            snippet_group=snippet_group,
            identifiers=identifiers,
            layout_options=layout_options)

    def image(self, identifiers, start_date, end_date,
              width=380.0, height=250.0, layout_extra=None):

        today = datetime.datetime.now()
        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)

        graph.add_today()
        return graph.http_png()

