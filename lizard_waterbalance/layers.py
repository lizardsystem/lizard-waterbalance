import datetime
import logging
import mapnik
from django.conf import settings
from django.contrib.gis.geos import Point

from lizard_map.adapter import Graph
from lizard_map.animation import AnimationSettings
from lizard_map.coordinates import google_to_wgs84
from lizard_map.coordinates import WGS84
from lizard_map.workspace import WorkspaceItemAdapter
from lizard_waterbalance.models import Parameter
from lizard_waterbalance.models import WaterbalanceArea

logger = logging.getLogger(__name__)


class AdapterWaterbalance(WorkspaceItemAdapter):
    """Adapter for module LizardWaterbalance.

    Registered as adapter_waterbalance.

    Uses default database table "waterbalance_shape" as geo database.
    """

    is_animatable = True

    def __init__(self, *args, **kwargs):
        super(AdapterWaterbalance, self).__init__(*args, **kwargs)
        self.shape_tablename = 'waterbalance_shape'
        # Parameter is phosphate, inlaatwater, sluitfout or verblijftijd.
        self.parameter_id = int(self.layer_arguments['parameter'])
        self.parameter = Parameter.objects.get(pk=self.parameter_id)

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
        rule = mapnik_rule(255, 255, 0)
        mapnik_style.rules.append(rule)
        # Version 1: rules based on gid
        # for gid in range(100):
        #     rule = mapnik_rule(0, 10 * gid ,0, '[gid] = %d' % gid)
        #     mapnik_style.rules.append(rule)

        # Version 2: rules based on value, hard coded
        # rule = mapnik_rule(0, 255, 0, '[value] <= 75')
        # mapnik_style.rules.append(rule)
        # rule = mapnik_rule(255, 0, 0, '[value] > 75')
        # mapnik_style.rules.append(rule)

        # Version 3: the real thing
        rule = mapnik_rule(0, 255, 0, '[name] = \'Riekerpolder\'')
        mapnik_style.rules.append(rule)

        return mapnik_style

    def layer(self, layer_ids=None, request=None):
        """Return layer and styles for a parameter.

        request contains the animation settings.
        """
        layers = []
        styles = {}

        animation_settings = AnimationSettings(request)
        selected_date = animation_settings.info()['selected_date']

        # Version 1: select everything, no data, rd
        # table_view = ('(select the_geom, gid from %s) '
        #               'result_view' % (
        #         self.shape_tablename))
        #s = selected_date.strftime('%Y-%m-%d')

        # Version 2: test select data, rd
        # table_view = (
        #     '(select the_geom, gid, value from %s '
        #     'inner join lizard_waterbalance_timeseries '
        #     #'as timeseries '
        #     'on waterbalance_shape.gafnaam = lizard_waterbalance_timeseries.name '
        #     'inner join lizard_waterbalance_timeseriesevent '
        #     #'as timeseriesevent '
        #     'on lizard_waterbalance_timeseries.id = lizard_waterbalance_timeseriesevent.timeseries_id '
        #     'where lizard_waterbalance_timeseriesevent.time = \'%s\') '
        #     'result_view' % (
        #         self.shape_tablename, selected_date.strftime('%Y-%m-01')))

        # Version 3: the real thing, wgs84
        # Note: timeseries must be of local type. timestep=MONTH.
        table_view = (
            '(select area.geom, area.name, tsevent.value from '
            'lizard_waterbalance_waterbalancearea as area, '
            'lizard_waterbalance_waterbalanceconf as conf, '
            'lizard_waterbalance_waterbalancetimeserie as wbts, '
            'lizard_waterbalance_timeseries as ts, '
            'lizard_waterbalance_timeseriesevent as tsevent '
            'where conf.waterbalance_area_id = area.id '
            'and wbts.configuration_id = conf.id '
            'and wbts.parameter_id = %d '
            'and wbts.local_timeseries_id = ts.id '
            'and wbts.timestep = 2 '  # MONTH
            'and ts.id = tsevent.timeseries_id '
            'and tsevent.time = \'%s\''
            ') '
            'result_view' % (
                self.parameter_id, selected_date.strftime('%Y-%m-01')))

        mapnik_style = self._mapnik_style()

        lyr = mapnik.Layer('Geometry from PostGIS')
        lyr.srs = WGS84
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
        wgs84_x, wgs84_y = google_to_wgs84(x, y)
        results = [
            {'distance': 0,
             'name': area.name,
             'shortname': area.name,
             'workspace_item': self.workspace_item,
             'identifier': {'area_id': area.id},
             'object': area}
            for area in WaterbalanceArea.objects.filter(
                geom__contains=Point(wgs84_x, wgs84_y))]
        # rd_x, rd_y = google_to_rd(x, y)
        # results = [
        #     {'distance': 0,
        #      'name': wb_shape.gafnaam,
        #      'shortname': wb_shape.gafnaam,
        #      'workspace_item': self.workspace_item,
        #      'identifier': {
        #             'area_name': wb_shape.gafnaam
        #             },
        #      'object': wb_shape}
        #     for wb_shape in WaterbalanceShape.objects.filter(
        #         the_geom__contains=Point(rd_x, rd_y))]
        return results

    def symbol_url(self, identifier=None, start_date=None,
                   end_date=None, icon_style=None):
        """
        Returns symbol.
        """
        icon_style = {'icon': 'waterbalance.png',
                      'mask': ('mask.png', ),
                      'color': (1, 0, 0, 0)}

        return super(AdapterWaterbalance, self).symbol_url(
            identifier=identifier,
            start_date=start_date,
            end_date=end_date,
            icon_style=icon_style)

    def location(self, area_id=None, layout=None):
        area = WaterbalanceArea.objects.get(pk=area_id)
        result = {
            'name': area.name,  # This is displayed in the popup
            'identifier': {'area_id': area_id}}
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

        line_styles = self.line_styles(identifiers)
        today = datetime.datetime.now()

        for identifier in identifiers:
            logger.debug('identifier: %s' % identifier)
            area_id = identifier['area_id']
            logger.debug(WaterbalanceArea.objects.filter(pk=area_id))

            # timeseries = Timeseries.objects.get(name='De Nieuwe Bullewijk')
            # dates = []
            # values = []
            # for ts_event in timeseries.timeseries_events.all().order_by(
            #     'time'):

            #     dates.append(ts_event.time)
            #     values.append(ts_event.value)
            # graph.axes.plot(dates, values,
            #                 lw=1,
            #                 color=line_styles[str(identifier)]['color'],
            #                 label=timeseries.name)

            # graph.axes.fill_between(
            #     dates, values, [value-10 for value in values],
            #     color='b', alpha=0.5)

        graph.add_today()
        return graph.http_png()
