# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

# Create your views here.

import datetime
import logging
import random
import time

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.lines import Line2D
import mapnik
import pkg_resources

from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map.adapter import Graph
from lizard_map.daterange import current_start_end_dates
from lizard_map.daterange import DateRangeForm
from lizard_map.models import Workspace
from lizard_waterbalance.concentration_computer import ConcentrationComputer
from lizard_waterbalance.management.commands.compute_waterbalance import create_waterbalance_computer
from lizard_waterbalance.models import Concentration
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceLabel
from lizard_waterbalance.timeseriesstub import TimeseriesStub
from lizard_waterbalance.timeseriesstub import create_from_file
from lizard_waterbalance.timeseriesstub import grouped_event_values
from lizard_waterbalance.timeseriesstub import multiply_timeseries

# We use the following values to uniquely identify the workspaces for
# 1. the general home page and
# 2. the waterbalance overview page.
# To make sure these values, which are primary keys, do not accidently
# identify a dynamically generated workspace, we have to define the
# two workspaces in the database in advance.
WATERBALANCE_HOMEPAGE_KEY = 2
WATERBALANCE_HOMEPAGE_NAME = "Waterbalance homepage"
CRUMB_HOMEPAGE = {'name': 'home', 'url': '/'}
GRAPH_TYPES = (
    ('waterbalans', u'Waterbalans'),
    ('waterpeil', u'Waterpeil'),
    ('waterpeil_met_sluitfout', u'Waterpeil met sluitfout'),
    ('cumulatief_debiet', u'Cumulatief debiet'),
    ('fracties_chloride', u'Fracties Chloride'),
    ('fracties_fosfaat', u'Fracties Fosfaat'),
    ('fosfaatbelasting', u'Fosfaatbelasting'),
)
IMPLEMENTED_GRAPH_TYPES = (
    'waterbalans',
    'fracties_chloride',
    'fracties_fosfaat',
    'fosfaatbelasting',
    )
BAR_WIDTH = {'year': 360,
             'month': 28,
             'day': 1}

logger = logging.getLogger(__name__)


def waterbalance_graph_data(area, start_datetime, end_datetime, recalculate=False):
    """Return the outcome needed for drawing the waterbalance graphs."""
    cache_key = '%s_%s_%s' % (area, start_datetime, end_datetime)
    t1 = time.time()
    result = cache.get(cache_key)
    if (result is None) or recalculate:
        fews_data_filename = pkg_resources.resource_filename(
            "lizard_waterbalance", "testdata/timeserie.csv")
        waterbalance_area, waterbalance_computer = create_waterbalance_computer(
            area, start_datetime, end_datetime, fews_data_filename)
        bucket2outcome, level_control, outcome = waterbalance_computer.compute(
            waterbalance_area, start_datetime, end_datetime)
        result = outcome
        cache.set(cache_key, result, 8 * 60 * 60)
        logger.debug("Stored waterbalance graph data in cache for %s", cache_key)
    else:
        logger.debug("Got waterbalance graph data from cache")
    t2 = time.time()
    logger.debug("Grabbing waterbalance data took %s seconds.", t2 - t1)
    return result


class TopHeight:
    """Maintains the height of the top of each bar in a stacked bar chart.

    Instance variable:
    * key_to_height -- dictionary that maps each bar to its total height

    Each bar is identified by a key, which often is its horizontal position in
    the chart. Let key be such anidentifier, then key_to_height[key] specifies
    the total height of the bar.

    """
    def __init__(self):
        self.key_to_height = {}

    def stack_bars(self, keys, heights):
        """Sets or update the heights for the given bars.

        Parameters:
        * keys -- list of bar keys
        * heights -- list of additional bar heights

        """
        for key, height in zip(keys, heights):
            self.key_to_height.setdefault(key, 0)
            self.key_to_height[key] += height

    def get_heights(self, keys):
        """Return the list of heights for the given bars.

        Parameters:
        * keys -- list of bar keys

        When a specified key is not present, this method returns 0 for that
        key.

        """
        heights = []
        for key in keys:
            heights.append(self.key_to_height.get(key, 0))

        return heights


class MonthlyDischarge:

    def retrieve_incoming(self):
        """Return the incoming monthly discharge.

        This method returns the incoming monthly discharge as a dictionary of
        parameter labels to a TimeseriesStub.

        """
        pass

    def retrieve_outgoing(self):
        """Return the outgoing monthly discharge.

        This method returns the incoming monthly discharge as a dictionary of
        parameter labels to a TimeseriesStub. In order to draw the plots for
        the outgoing discharge in the opposite direction of the plots for the
        incoming discharge, the sign of the values should be negative.

        """
        pass


matplotlib_colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']


class MonthlyDischargeStub(MonthlyDischarge):

    def retrieve_incoming(self):
        incoming_discharge = {}
        months = range(1, 12)
        times = [datetime.date(2009, m, 1) for m in months]

        timeseries = TimeseriesStub(0)
        values = [random.randrange(5000, 10000) for m in months]
        for time, value in zip(times, values):
            timeseries.add_value(time, value)
        incoming_discharge["inlaat"] = timeseries

        timeseries = TimeseriesStub(0)
        values = [random.randrange(5000, 10000) for m in months]
        for time, value in zip(times, values):
            timeseries.add_value(time, value)
        incoming_discharge["neerslag"] = timeseries

        return incoming_discharge

    def retrieve_outgoing(self):
        outgoing_discharge = {}
        months = range(1, 12)
        times = [datetime.date(2009, m, 1) for m in months]

        timeseries = TimeseriesStub(0)
        values = [-1 * random.randrange(500, 1500) for m in months]
        for time, value in zip(times, values):
            timeseries.add_value(time, value)
        outgoing_discharge["sluitfout tov gemaal"] = timeseries

        timeseries = TimeseriesStub(0)
        values = [-1 * random.randrange(500, 1500) for m in months]
        for time, value in zip(times, values):
            timeseries.add_value(time, value)
        outgoing_discharge["maalstaat"] = timeseries

        return outgoing_discharge

class MonthlyDischargeFromFile(MonthlyDischarge):

    def __init__(self, name_to_extract, label2incoming):
        self.name_to_extract = name_to_extract
        self.label2incoming = label2incoming

    def read_from_file(self, filename):

        self.dictionary = create_from_file(filename)

    def retrieve_incoming(self):

        incoming_discharge = {}
        for name, label2timeseries in self.dictionary.items():
            if name == self.name_to_extract:
                for label, timeseries in label2timeseries.items():
                    try:
                        if self.label2incoming[label]:
                            incoming_discharge[label] = timeseries
                    except KeyError:
                        pass
        return incoming_discharge

    def retrieve_outgoing(self):

        outgoing_discharge = {}
        for name, label2timeseries in self.dictionary.items():
            if name == self.name_to_extract:
                for label, timeseries in label2timeseries.items():
                    try:
                        if not self.label2incoming[label]:
                            outgoing_discharge[label] = timeseries
                    except KeyError:
                        pass
        return outgoing_discharge


def indicator_graph(request,
                    area=None,
                    id=None):
    class MockTimeserie(object):
        class MockTimeSerieData(object):
            def all(self):
                return []
        name = 'geen tijdreeks beschikbaar'
        timeseriedata = MockTimeSerieData()


def waterbalance_start(request,
                       template='lizard_waterbalance/waterbalance-overview.html',
                       crumbs_prepend=None):
    """Show waterbalance overview workspace.

    The workspace for the waterbalance homepage should already be present.

    Parameters:
    * crumbs_prepend -- list of breadcrumbs

    """
    waterbalance_areas = WaterbalanceArea.objects.all()

    if crumbs_prepend is None:
        crumbs = [{'name': 'home', 'url': '/'}]
    else:
        crumbs = crumbs_prepend
    crumbs.append({'name': 'Waterbalans overzicht',
                   'title': 'Waterbalans overzicht',
                   'url': reverse('waterbalance_start')})

    special_homepage_workspace = \
        get_object_or_404(Workspace, pk=WATERBALANCE_HOMEPAGE_KEY)
    return render_to_response(
        template,
        {'waterbalance_areas': waterbalance_areas,
         'workspaces': {'user': [special_homepage_workspace]},
         'javascript_hover_handler': 'popup_hover_handler',
         'javascript_click_handler': 'waterbalance_area_click_handler',
         'crumbs': crumbs},
        context_instance=RequestContext(request))


def waterbalance_area_summary(request,
                              area=None,
                              template='lizard_waterbalance/waterbalance_area_summary.html',
                              crumbs_prepend=None):
    """Show the summary page of the named WaterbalanceArea.

    Parameters:
    * area -- name of the WaterbalanceArea whose summary has to be shown
    * crumbs_prepend -- list of breadcrumbs

    """
    waterbalance_area = get_object_or_404(WaterbalanceArea, slug=area)

    date_range_form = DateRangeForm(
        current_start_end_dates(request, for_form=True))

    if crumbs_prepend is None:
        crumbs = [{'name': 'home', 'url': '/'}]
    else:
        crumbs = crumbs_prepend
    kwargs = {'area': waterbalance_area.slug}
    crumbs.append({'name': waterbalance_area.name,
                   'title': waterbalance_area.name,
                   'url': reverse('waterbalance_area_summary', kwargs=kwargs)})

    graph_type_formitems = []
    for index, (graph_type, name) in enumerate(GRAPH_TYPES):
        formitem = {}
        formitem['id'] = 'id_graph_type_%s' % index
        formitem['value'] = graph_type
        formitem['label'] = name
        formitem['disabled'] = (graph_type not in IMPLEMENTED_GRAPH_TYPES)
        graph_type_formitems.append(formitem)
    periods = [('year', 'Per jaar', False),
               ('month', 'Per maand', True),
               ('day', 'Per dag', False)]

    return render_to_response(
        template,
        {'waterbalance_area': waterbalance_area,
         'date_range_form': date_range_form,
         'graph_type_formitems': graph_type_formitems,
         'periods': periods,
         'crumbs': crumbs},
        context_instance=RequestContext(request))


def get_timeseries(timeseries, start, end, period='month'):
    """Return the events for the given timeseries in the given range.

    Parameters:
    * timeseries -- implementation of a time series that supports a method events()
    * start -- the earliest date (and/or time) of a returned event
    * end -- the latest date (and/or time) of a returned event
    * period -- 'year', 'month' or 'day'

    """
    return zip(*(e for e in grouped_event_values(timeseries, period) 
                 if e[0] >= start and e[0] < end))


def get_average_timeseries(timeseries, start, end, period='month'):
    """Return the events for the given timeseries in the given range.

    Parameters:
    * timeseries -- implementation of a time series that supports a method events()
    * start -- the earliest date (and/or time) of a returned event
    * end -- the latest date (and/or time) of a returned event
    * period -- 'year', 'month' or 'day'

    """
    return zip(*(e for e in grouped_event_values(timeseries, period, average=True) 
                 if e[0] >= start and e[0] < end))


def draw_bar(callable, axes, times, values, bar_width, color, bottom):

    callable(times, values, bar_width, color=color, bottom=bottom)


def get_timeseries_label(name):
    """Return the WaterbalanceLabel wth the given name."""
    return WaterbalanceLabel.objects.get(name__iexact=name)


def retrieve_horizon(request):
    """Return the start and end datetime.datetime on the horizontal axis.

    The user selects the start and end date but not the date and time. This method returns
    the start date at 00:00 and the end date at 23:59:59.

    """
    start_date, end_date = current_start_end_dates(request)
    start_datetime = datetime.datetime(start_date.year,
                                       start_date.month,
                                       start_date.day,
                                       0,
                                       0,
                                       0)
    end_datetime = datetime.datetime(end_date.year,
                                     end_date.month,
                                     end_date.day,
                                     23,
                                     59,
                                     59)
    return start_datetime, end_datetime

def waterbalance_area_graph(request,
                            name,
                            area=None,
                            graph_type=None):
    """Draw the graph for the given area and of the given type."""

    period = request.GET.get('period', 'month')
    start_datetime, end_datetime = retrieve_horizon(request)
    start_date = start_datetime.date()
    end_date = end_datetime.date() + datetime.timedelta(1)

    width = request.GET.get('width', 1600)
    height = request.GET.get('height', 400)
    krw_graph = Graph(start_date, end_date, width, height)

    krw_graph.suptitle("Waterbalans")

    # Show line for today.
    krw_graph.add_today()

    bar_width = BAR_WIDTH[period]

    outcome = waterbalance_graph_data(area, start_datetime, end_datetime)

    t1 = time.time()

    incoming_bars = [
        ("verhard", outcome.open_water_timeseries["hardened"]),
        ("gedraineerd", outcome.open_water_timeseries["drained"]),
        ("afstroming", outcome.open_water_timeseries["flow_off"]),
        ("uitspoeling", outcome.open_water_timeseries["undrained"]),
        ("neerslag", outcome.open_water_timeseries["precipitation"]),
        ("kwel", outcome.open_water_timeseries["seepage"]),
        ]

    intakes = PumpingStation.objects.filter(into=True, computed_level_control=False)
    for intake in intakes.order_by('name'):
        incoming_bars.append((intake.name, intake.retrieve_sum_timeseries()))

    intakes = PumpingStation.objects.filter(into=True, computed_level_control=True)
    for intake in intakes.order_by('name'):
        incoming_bars.append((intake.name, outcome.level_control_assignment[intake]))

    outgoing_bars = [
        ("intrek", outcome.open_water_timeseries["indraft"]),
        ("verdamping", outcome.open_water_timeseries["evaporation"]),
        ("wegzijging", outcome.open_water_timeseries["infiltration"]),
         ]

    pumps = PumpingStation.objects.filter(into=False, computed_level_control=False)
    for pump in pumps.order_by('name'):
        outgoing_bars.append((pump.name, pump.retrieve_sum_timeseries()))

    pumps = PumpingStation.objects.filter(into=False, computed_level_control=True)
    for pump in pumps.order_by('name'):
        outgoing_bars.append((pump.name, outcome.level_control_assignment[pump]))

    names = [bar[0] for bar in incoming_bars + outgoing_bars]
    colors = ['#' + get_timeseries_label(name).color for name in names]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    krw_graph.legend_space()
    krw_graph.legend(handles, names)

    for bars in [incoming_bars, outgoing_bars]:
        top_height = TopHeight()
        for bar in bars:
            label = get_timeseries_label(bar[0])
            times, values = get_timeseries(bar[1], start_datetime, end_datetime,
                                           period=period)

            # add the following keyword argument to give the bar edges the same
            # color as the bar itself: edgecolor='#' + label.color

            color = '#' + label.color
            bottom = top_height.get_heights(times)
            krw_graph.axes.bar(times, values, bar_width, color=color, edgecolor=color,
                               bottom=bottom)
            top_height.stack_bars(times, values)

    t2 = time.time()
    logger.debug("Grabbing all graph data took %s seconds.", t2 - t1)

    canvas = FigureCanvas(krw_graph.figure)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def waterbalance_fraction_distribution(request,
                                       name,
                                       area=None,
                                       graph_type=None):
    """Draw the graph for the given area and of the given type."""

    period = request.GET.get('period', 'month')
    start_datetime, end_datetime = retrieve_horizon(request)
    start_date = start_datetime.date()
    end_date = end_datetime.date() + datetime.timedelta(1)

    width = request.GET.get('width', 1600)
    height = request.GET.get('height', 400)
    krw_graph = Graph(start_date, end_date, width, height)
    ax2 = krw_graph.axes.twinx()

    if graph_type == 'fracties_chloride':
        substance = Concentration.SUBSTANCE_CHLORIDE
    else:
        substance = Concentration.SUBSTANCE_PHOSPHATE

    title = "Fractieverdeling "
    if substance == Concentration.SUBSTANCE_CHLORIDE:
        title += "chloride"
    else:
        title += "fosfaat"
    krw_graph.suptitle(title)

    # Show line for today.
    krw_graph.add_today()

    bar_width = BAR_WIDTH[period]

    outcome = waterbalance_graph_data(area, start_datetime, end_datetime)
    waterbalance_area = WaterbalanceArea.objects.get(slug=area)

    t1 = time.time()

    bars = [("berging", outcome.open_water_fractions["initial"], None),
            ("neerslag",
             outcome.open_water_fractions["precipitation"],
             waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact='neerslag').minimum),
            ("kwel",
             outcome.open_water_fractions["seepage"],
             waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact='kwel').minimum),
            ("verhard",
             outcome.open_water_fractions["hardened"],
             waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact='verhard').minimum),
            ("gedraineerd",
             outcome.open_water_fractions["drained"],
             waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact='gedraineerd').minimum),
            ("ongedraineerd",
             outcome.open_water_fractions["undrained"],
             waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact='ongedraineerd').minimum),
            ("afstroming",
             outcome.open_water_fractions["flow_off"],
             waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact='afstroming').minimum),
            ]

    intakes = PumpingStation.objects.filter(into=True, computed_level_control=False)
    for intake in intakes.order_by('name'):
        bars.append((intake.name,
                     outcome.intake_fractions[intake],
                     waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact=intake.name).minimum))

    intakes = PumpingStation.objects.filter(into=True, computed_level_control=True)
    for intake in intakes.order_by('name'):
        bars.append((intake.name,
                     outcome.intake_fractions[intake],
                     waterbalance_area.concentrations.get(substance__exact=substance, flow_name__iexact=intake.name).minimum))

    names = [bar[0] for bar in bars]
    if substance == Concentration.SUBSTANCE_CHLORIDE:
        names.append("chloride")
    else:
        names.append("fosfaat")

    colors = ['#' + get_timeseries_label(name).color for name in names]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    # we add the legend entries for the measured substance levels

    substance_color = colors[-1]
    handles.append(Line2D([], [], linestyle=' ',color=substance_color, marker='D'))
    substance_name = names[-1]
    names.append(substance_name + " meting")

    krw_graph.legend_space()
    krw_graph.legend(handles, names)

    times = []
    values = []
    top_height = TopHeight()
    for bar in bars:

        label = get_timeseries_label(bar[0])
        times, values = get_average_timeseries(bar[1], start_datetime, end_datetime,
                                               period=period)

        # add the following keyword argument to give the bar edges the same
        # color as the bar itself: edgecolor='#' + label.color

        color = '#' + label.color
        bottom = top_height.get_heights(times)
        krw_graph.axes.bar(times, values, bar_width, color=color, edgecolor=color,
                           bottom=bottom)
        top_height.stack_bars(times, values)

    fractions_list = [bar[1] for bar in bars[1:]]
    concentrations = [bar[2] for bar in bars[1:]]

    # show the computed substance levels
    substance_timeseries = ConcentrationComputer().compute(fractions_list,
                                                           outcome.open_water_timeseries["storage"],
                                                           concentrations)
    times, values = get_average_timeseries(substance_timeseries, start_datetime, end_datetime,
                                           period=period)

    ax2.plot(times, values, 'k-')

    # show the measured substance levels when they are present
    try:
        if substance == Concentration.SUBSTANCE_CHLORIDE:
            substance_timeseries = waterbalance_area.chloride
        else:
            substance_timeseries = waterbalance_area.phosphate
        times, values = get_average_timeseries(substance_timeseries,
                                               start_datetime,
                                               end_datetime,
                                               period=period)
        ax2.plot(times, values, 'k-')
    except AttributeError:
        logger.warning("Unable to retrieve measured time series for %s",
                       substance_name)

    t2 = time.time()

    logger.debug("Grabbing all graph data took %s seconds.", t2 - t1)

    canvas = FigureCanvas(krw_graph.figure)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def waterbalance_phosphate_impact(request,
                                  name,
                                  area=None,
                                  graph_type=None):
    """Draw the graph for the given area and of the given type."""

    period = request.GET.get('period', 'month')
    start_datetime, end_datetime = retrieve_horizon(request)
    start_date = start_datetime.date()
    end_date = end_datetime.date() + datetime.timedelta(1)

    width = request.GET.get('width', 1600)
    height = request.GET.get('height', 400)
    krw_graph = Graph(start_date, end_date, width, height)

    krw_graph.suptitle("Fosfaatbelasting, maandgemiddelde in [mg/m2/dag]")

    # Show line for today.
    krw_graph.add_today()

    bar_width = BAR_WIDTH[period]

    outcome = waterbalance_graph_data(area, start_datetime, end_datetime)
    waterbalance_area = WaterbalanceArea.objects.get(slug=area)

    phosphate = Concentration.SUBSTANCE_PHOSPHATE

    bars = [("neerslag (incr)", "neerslag (min)",
             outcome.open_water_timeseries["precipitation"],
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='neerslag').increment,
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='neerslag').minimum),
            ("kwel (incr)", "kwel (min)",
             outcome.open_water_timeseries["seepage"],
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='kwel').increment,
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='kwel').minimum),
            ("verhard (incr)", "verhard (min)",
             outcome.open_water_timeseries["hardened"],
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='verhard').increment,
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='verhard').minimum),
            ("gedraineerd (incr)", "gedraineerd (min)",
             outcome.open_water_timeseries["drained"],
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='gedraineerd').increment,
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='gedraineerd').minimum),
            ("ongedraineerd (incr)", "ongedraineerd (min)",
             outcome.open_water_timeseries["undrained"],
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='ongedraineerd').increment,
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='ongedraineerd').minimum),
            ("afstroming (incr)", "afstroming (min)",
             outcome.open_water_timeseries["flow_off"],
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='afstroming').increment,
             waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact='afstroming').minimum),
            ]


    intakes = PumpingStation.objects.filter(into=True, computed_level_control=False)
    for intake in intakes.order_by('name'):
        bars.append((intake.name + " (incr)",
                     intake.name + " (min)",
                     intake.retrieve_sum_timeseries(),
                     waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact=intake.name).increment,
                     waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact=intake.name).minimum))

    intakes = PumpingStation.objects.filter(into=True, computed_level_control=True)
    for intake in intakes.order_by('name'):
        bars.append((intake.name + " (incr)",
                     intake.name + " (min)",
                     outcome.level_control_assignment[intake],
                     waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact=intake.name).increment,
                     waterbalance_area.concentrations.get(substance__exact=phosphate, flow_name__iexact=intake.name).minimum))

    names = [bar[0] for bar in bars] + [bar[1] for bar in bars]
    colors = ['#' + get_timeseries_label(name).color for name in names]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    krw_graph.legend_space()
    krw_graph.legend(handles, names)

    open_water = waterbalance_area.open_water

    top_height = TopHeight()

    for index in range(2):
        for bar in bars:
            label = get_timeseries_label(bar[1-index])
            discharge = bar[2]

            if index == 0:
                concentration = bar[4]
            else:
                concentration = bar[3] + bar[4]
            # Concentration is specified in [mg/l] whereas discharge is
            # specified in [m3/day]. The impact is specified in [mg/m2/day] so
            # we first multiply the concentration by 1000 to specify it in
            # [mg/m3] and then divide the result by the surface of the open
            # water to specify it in [mg/m2/m3].
            concentration = (concentration * 1000.0) / open_water.surface

            impact_timeseries = multiply_timeseries(discharge, concentration)

            times, values = get_average_timeseries(impact_timeseries, start_datetime, end_datetime,
                                                   period=period)

            # add the following keyword argument to give the bar edges the same
            # color as the bar itself: edgecolor='#' + label.color

            color = '#' + label.color
            bottom = top_height.get_heights(times)
            krw_graph.axes.bar(times, values, bar_width, color=color, edgecolor=color,
                               bottom=bottom)
            top_height.stack_bars(times, values)

    canvas = FigureCanvas(krw_graph.figure)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


def waterbalance_area_graphs(request,
                             area=None,
                             graph_type=None):
    name = request.GET.get('name', "landelijk")
    if graph_type == 'waterbalans':
        return waterbalance_area_graph(request, name, area, graph_type)
    elif graph_type == 'fracties_chloride':
        return waterbalance_fraction_distribution(request, name, area, graph_type)
    elif graph_type == 'fracties_fosfaat':
        return waterbalance_fraction_distribution(request, name, area, graph_type)
    elif graph_type == 'fosfaatbelasting':
        return waterbalance_phosphate_impact(request, name, area, graph_type)


def waterbalance_shapefile_search(request):
    """Return url to redirect to if a waterbody is found.
    """
    google_x = float(request.GET.get('x'))
    google_y = float(request.GET.get('y'))

    # Set up a basic map as only map can search...
    mapnik_map = mapnik.Map(400, 400)
    mapnik_map.srs = coordinates.GOOGLE

    workspace = Workspace.objects.get(name=WATERBALANCE_HOMEPAGE_NAME)
    first_workspace_item = workspace.workspace_items.all()[0]
    adapter = first_workspace_item.adapter

    search_results = adapter.search(google_x, google_y)
    # Return url of first found object.
    for search_result in search_results:
        id_in_shapefile = search_result['identifier']['id']
        waterbalance_area = \
            WaterbalanceArea.objects.get(name=id_in_shapefile)
        return HttpResponse(waterbalance_area.get_absolute_url())

    # Nothing found? Return an empty response and the javascript popup handler
    # will fire.
    return HttpResponse('')


def graph_select(request):
    """
    Processes ajax call, return appropriate png urls.
    """

    graphs = []
    if request.is_ajax():
        area_slug = request.POST['area']
        selected_graph_types = request.POST.getlist('graphs')
        period = request.POST['period']

        for graph_type, name in GRAPH_TYPES:
            if not graph_type in selected_graph_types:
                continue
            url = (reverse('waterbalance_area_graph',
                           kwargs={'area': area_slug,
                                   'graph_type': graph_type}) +
                   '?period=' + period)
            graphs.append(url)
        json = simplejson.dumps(graphs)
        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponse("Should not be run this way.")


def create_location_label(location):
    return location.name + ", pkey %d" % location.lkey


def search_fews_lkeys(request):
    if request.is_ajax():
        pkey = request.POST['pkey']
        fkey = request.POST['fkey']
        timeseries = Timeserie.objects.filter(parameterkey=pkey, filterkey=fkey)
        timeseries = timeseries.distinct().order_by("locationkey")
        lkeys = [(ts.locationkey.lkey, create_location_label(ts.locationkey)) for ts in timeseries]
        print lkeys
        json = simplejson.dumps(lkeys)
        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponse("Should not be run this way.")


def recalculate_graph_data(request, area=None):
    """Recalculate the graph data by emptying the cache."""
    if request.method == "POST":
        start_datetime, end_datetime = (datetime.datetime(1996, 1, 1),
                                        datetime.datetime(2010, 6, 30))
        outcome = waterbalance_graph_data(area, start_datetime, end_datetime,
                                          recalculate=True)
        # # Enable this later when there's ajax integration
        # if request.is_ajax():
        #     json = simplejson.dumps("Success")
        #     return HttpResponse(json, mimetype='application/json')
        return HttpResponseRedirect(
            reverse('waterbalance_area_summary', kwargs={'area': area}))
    else:
        return HttpResponse("false")
