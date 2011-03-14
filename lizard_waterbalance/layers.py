import logging
import mapnik
from django.conf import settings

from lizard_map.adapter import Graph
from lizard_map.coordinates import GOOGLE
from lizard_map.workspace import WorkspaceItemAdapter

logger = logging.getLogger(__name__)


class AdapterWaterbalance(WorkspaceItemAdapter):
    """Adapter for module LizardWaterbalance.

    Registered as adapter_waterbalance.

    Uses default database table "waterbalance_shape" as geo database.
    """

    def __init__(self, *args, **kwargs):
        super(AdapterWaterbalance, self).__init__(*args, **kwargs)
        self.shape_tablename = 'waterbalance_shape'



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

            symb_line = mapnik.LineSymbolizer(mapnik_color, 3)
            rule.symbols.append(symb_line)

            symb_poly = mapnik.PolygonSymbolizer(mapnik_color)
            symb_poly.fill_opacity = 0.5
            rule.symbols.append(symb_poly)
            return rule

        mapnik_style = mapnik.Style()
        rule = mapnik_rule(255, 0 ,0)
        mapnik_style.rules.append(rule)
        return mapnik_style


    def layer(self, layer_ids=None, request=None):
        """Return layer and styles for a parameter.
        """
        layers = []
        styles = {}

        table_view = ('(select the_geom, objectid from %s) '
                      '%s' % (
                self.shape_tablename, self.shape_tablename))
        mapnik_style = self._mapnik_style()

        lyr = mapnik.Layer('Geometry from PostGIS')
        lyr.srs = GOOGLE
        BUFFERED_TABLE = table_view
        db_settings = settings.DATABASES['default']
        lyr.datasource = mapnik.PostGIS(
            host=db_settings['HOST'],
            user=db_settings['USER'],
            password=db_settings['PASSWORD'],
            dbname=db_settings['NAME'],
            table=str(BUFFERED_TABLE))

        layers.append(lyr)
        styles['waterbalance_style'] = mapnik_style

        return layers, styles

    def search(self, x, y, radius=None):
        results = []
        return results

    def symbol_url(self, identifier=None, start_date=None,
                   end_date=None, icon_style=None):
        """
        Returns symbol.
        """
        return super(AdapterWaterbalance, self).symbol_url()
            # identifier=identifier,
            # start_date=start_date,
            # end_date=end_date,
            # icon_style=icon_style)

    def location(self, parameter):
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

