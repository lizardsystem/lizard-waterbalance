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
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceTimeserie
from lizard_waterbalance.models import TimeseriesEvent

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

        if self.request:
            animation_settings = AnimationSettings(self.request)
            self.selected_date = animation_settings.info()['selected_date']
        else:
            self.selected_date = None

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
        step_size = 1000000
        for step in range(12):
            rule_str = '[value] >= %d and [value] < %d' % (
                step*step_size, (step+1)*step_size)
            rule = mapnik_rule(0, step*20, 0, rule_str)
            mapnik_style.rules.append(rule)

        return mapnik_style

    def _timeseries(
        self, area,
        timestep=WaterbalanceTimeserie.TIMESTEP_MONTH):
        """
        return corresponding waterbalance timeseries object.

        If nothing found, return None
        """
        configurations = WaterbalanceConf.objects.filter(
            waterbalance_area=area)
        wb_ts = WaterbalanceTimeserie.objects.filter(
            parameter=self.parameter,
            configuration__in=list(configurations),
            timestep=timestep)
        if wb_ts:
            # There should be only one per scenario. There should be
            # only one scenario. So just take the first.
            return wb_ts[0].get_timeseries()
        return None

    def layer(self, layer_ids=None, request=None):
        """Return layer and styles for a parameter.

        Requires request.
        request contains the animation settings.

        Set self.selected_date
        """
        layers = []
        styles = {}

        if not request:
            return layers, styles

        # Note: timeseries must be of local type. timestep=MONTH.
        # TODO: time format is hardcoded. Must work for oracle as well.
        # TODO: add scenario
        table_view = (
            '(select area.geom, area.name, tsevent.value as value from '
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
                self.parameter_id, self.selected_date.strftime('%Y-%m-01')))

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
        """Search on x, y and return found objects.

        Name is displayed in mouse hover.

        parameter + config (area) + (scenario) + timestep

        if self.selected_date is present: display value.
        """
        if self.selected_date is None:
            logger.error('There is no self.selected_date.')
            return []
        wgs84_x, wgs84_y = google_to_wgs84(x, y)

        # Is always 0 or 1
        areas = WaterbalanceArea.objects.filter(
            geom__contains=Point(wgs84_x, wgs84_y))

        if not areas:
            return []

        area = areas[0]

        # Add value to the name

        # Find corresponding timeseries for areas, parameter
        ts = self._timeseries(area)

        # Look up value
        if ts:
            selected_date_rounded = datetime.date(
                self.selected_date.year,
                self.selected_date.month, 1)
            try:
                ts_event = (
                    ts.timeseries_events.get(
                        time=selected_date_rounded))
                name = '%s - %s=%.2f' % (
                    area.name, self.parameter, ts_event.value)
            except TimeseriesEvent.DoesNotExist:
                # No value found - do nothing
                return []

        # We can only arrive here when the corresponding area has data.
        return [
            {'distance': 0,
             'name': name,
             'shortname': area.name,
             'workspace_item': self.workspace_item,
             'identifier': {'area_id': area.id},
             'object': area}]

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

        if self.selected_date:
            today = self.selected_date
        else:
            today = datetime.datetime.now()
        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)

        line_styles = self.line_styles(identifiers)

        for identifier in identifiers:
            logger.debug('identifier: %s' % identifier)
            area = WaterbalanceArea.objects.get(pk=identifier['area_id'])

            # Try to fetch day timeseries.
            ts = self._timeseries(area, WaterbalanceTimeserie.TIMESTEP_DAY)
            if ts is None:
                # Revert to default: month.
                ts = self._timeseries(area)

            if ts:
                dates = []
                values = []
                for ts_event in ts.timeseries_events.filter(
                    time__gte=start_date, time__lte=end_date).order_by(
                    'time'):

                    dates.append(ts_event.time)
                    values.append(ts_event.value)
                graph.axes.plot(dates, values,
                                lw=1,
                                color=line_styles[str(identifier)]['color'],
                                label=ts.name)

            # graph.axes.fill_between(
            #     dates, values, [value-10 for value in values],
            #     color='b', alpha=0.5)

        graph.add_today()
        return graph.http_png()
