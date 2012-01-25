# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

# Create your views here.

from datetime import datetime
from datetime import time as datetime_time
from datetime import timedelta
import logging
from time import gmtime
from time import strftime
from time import time

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.utils import simplejson
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.lines import Line2D
import mapnik

from dbmodel.models import Area
from dbmodel.models import PumpingStation
from lizard_fewsunblobbed.models import Timeserie
from lizard_map import coordinates
from lizard_map.adapter import Graph
from lizard_map.daterange import current_start_end_dates
from lizard_map.models import Workspace
from lizard_wbcomputation.compute import WaterbalanceComputer2
from lizard_waterbalance.forms import WaterbalanceConfEditForm
from lizard_waterbalance.forms import OpenWaterEditForm
from lizard_waterbalance.forms import PumpingStationEditForm
from lizard_waterbalance.forms import create_location_label
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import Label
from lizard_waterbalance.models import Parameter
from timeseries.timeseriesstub import TimeseriesStub
from timeseries.timeseriesstub import add_timeseries
from timeseries.timeseriesstub import cumulative_event_values
from timeseries.timeseriesstub import grouped_event_values
from timeseries.timeseriesstub import write_to_pi_file

import hotshot
import os

try:
    import settings
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE
except:
    PROFILE_LOG_BASE = "/tmp"


date2datetime = lambda d: datetime(d.year, d.month, d.day)

# When the name of a legend entry is too long, the legend might overlap the
# graph. See ticket 3191 for details.

MAX_LEGEND_NAME_LENGTH = 24


def abridged_legend_name(name, maximum_length = MAX_LEGEND_NAME_LENGTH ):
    """Return an abridged version of the given name.

    The abridged name will not exceed the MAX_LEGEND_NAME_LENGTH.

    """
    if len(name) > maximum_length:
        name = name[:maximum_length - 1] + "."
    return name


def extended_legend_name(name, extension):
    """Return an abridged version of the given name with the given extension.

    """
    maximum_length = MAX_LEGEND_NAME_LENGTH - len(extension)
    return abridged_legend_name(name, maximum_length) + extension


def configuration_edit(request, template=None):
    if template is None:
        template = 'lizard_waterbalance/configuration.html'

    return render_to_response(
        template,
        { },
        context_instance=RequestContext(request))



def profile(log_file):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the
    file name, such that 'my_view.prof' become 'my_view-20100211T170321.prof',
    where the time stamp is in UTC. This makes it easy to run and compare
    multiple trials.
    """

    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    def _outer(f):
        def _inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            (base, ext) = os.path.splitext(log_file)
            base = base + "-" + strftime("%Y%m%dT%H%M%S", gmtime())
            final_log_file = base + ext

            prof = hotshot.Profile(final_log_file)
            try:
                ret = prof.runcall(f, *args, **kwargs)
            finally:
                prof.close()
            return ret

        return _inner
    return _outer

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
    ('fosfaatbelasting', u'Fosfaatbelasting'),
)
IMPLEMENTED_GRAPH_TYPES = (
    'waterbalans',
    'waterpeil',
    'waterpeil_met_sluitfout',
    'cumulatief_debiet',
    'fracties_chloride',
    'fosfaatbelasting',
    )

INITIAL_SELECTED_GRAPH_TYPES = (
    'waterbalans',
    'fracties_chloride',
    )
BAR_WIDTH = {'year': 364,
             'hydro_year': 364,
             'quarter': 90,
             'month': 30,
             'day': 1}

colors_list = ['yellow', 'green', 'black', 'grey', 'purple', 'blue', 'red',
               'pink']

# Exceptions for boolean fields: used in tab edit forms.
# Key is the field name, value is text used for (True, False).
TRUE_FALSE_EXCEPTIONS = {
    'computed_level_control': ('Berekend', 'Opgedrukt'),
    }

logger = logging.getLogger(__name__)


class TopHeight:
    """Maintains the height of the top of each bar in a stacked bar chart.

    Instance variable:
    * key_to_height -- dictionary that maps each bar to its total height

    Each bar is identified by a key, which often is its horizontal position in
    the chart. Let key be such an identifier, then key_to_height[key] specifies
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


def indicator_graph(request,
                    area=None,
                    id=None):
    class MockTimeserie(object):
        class MockTimeSerieData(object):
            def all(self):
                return []
        name = 'geen tijdreeks beschikbaar'
        timeseriedata = MockTimeSerieData()

def retrieve_viewable_configurations(user):
    """Return the Queryset of WaterbalanceConf the given user is allowed to see.

    """
    configurations = \
        WaterbalanceConf.objects.filter(waterbalance_area__active=True,
                                        waterbalance_scenario__active=True)
    if not user.has_perm("lizard_waterbalance.see_not_public_scenarios"):
        configurations = \
            configurations.filter(waterbalance_scenario__public=True)

    configurations.order_by('waterbalance_area__name',
        'waterbalance_scenario__order').select_related('WaterbalanceArea',
            'WaterbalanceScenario')

    return configurations


class DataForCumulativeGraph:
    """Prepares the cumulative events for drawing.

    The cumulative events as calculated do not correspond to the data points in
    the graph. For example, the date of each cumulative event is the first day
    of each period. However, as as the events contain cumulative values, they
    should be drawn at the end of each period. An object of this class
    prepares the data for drawing.

    Instance variables:
      * dates *
        sequence of datetime objects
      * values
        sequence of values, one for each date

    """

    def __init__(self, dates, values):
        self.dates = dates
        self.values = values

    def retrieve_for_drawing(self, period, reset_period):
        """Return copies of the stored events but suitable for drawing."""
        dates = self.move_forward(self.dates, period)
        dates, values = self.insert_restart(dates, self.values, reset_period)
        return dates, values

    def move_forward(self, dates, period):
        """Return a copy of the dates moved to the last second of its period.

        The date of each event is the first day of each period but as the
        corresponding values are cumulative, they should be drawn at the end of
        each period. This method returns a list of copies of each date where
        each copy is moved to the last second of the period.

        """
        last_time = datetime_time(23, 59, 59)
        if period == 'day':
            result = [datetime.combine(date, last_time) for date in dates]
        elif period == 'month':
            result = []
            for date in dates:
                new_month = date.month + 1
                month = (new_month - 1) % 12 + 1
                year = date.year + (new_month - 1) / 12
                new_date = datetime(year, month, date.day) - \
                           timedelta(1)
                result.append(datetime.combine(new_date, last_time))
        elif period == 'quarter':
            result = []
            for date in dates:
                new_month = date.month + 3
                month = (new_month - 1) % 12 + 1
                year = date.year + (new_month - 1) / 12
                new_date = datetime(year, month, date.day) - \
                           timedelta(1)
                result.append(datetime.combine(new_date, last_time))
        elif period == 'year' or period == 'hydro_year':
            result = []
            for date in dates:
                new_date = datetime(date.year + 1, date.month, date.day) - \
                           timedelta(1)
                result.append(datetime.combine(new_date, last_time))
        return result

    def insert_restart(self, dates, values, reset_period):
        """Return the pair of copied dates and values with an additional reset.

        A reset is an event that resets the cumulative dates and values to the
        value 0.0 at a specific date and time. This function inserts such a
        reset at the start of each reset period.

        """
        new_dates, new_values = [], []
        previous_date = None
        for date, value in zip(dates, values):
            if not previous_date is None:
                first_date = self.first_date(date, reset_period)
                if previous_date < first_date and first_date <= date:
                    new_dates.append(first_date)
                    new_values.append(0.0)
            new_dates.append(date)
            new_values.append(value)
            previous_date = date
        return new_dates, new_values

    def first_date(self, date, reset_period):
        if reset_period == 'month':
            date = datetime(date.year, date.month, 1)
        elif reset_period == 'quarter':
            month = 1 + ((date.month - 1) / 3 * 3)
            date = datetime(date.year, month, 1)
        elif reset_period == 'hydro_year':
            if date.month > 9:
                date = datetime(date.year, 10, 1)
            else:
                date = datetime(date.year - 1, 10, 1)
        elif reset_period == 'year':
            date = datetime(date.year, 1, 1)
        return date

def raw_add_timeseries(timeserie_a, timeserie_b):
    if next(timeserie_a.raw_events(), None) is None:
        result = timeserie_b
    elif next(timeserie_b.raw_events(), None) is None:
        result = timeserie_a
    else:
        result = TimeseriesStub()
        events_a = list(timeserie_a.raw_events())
        index_a = 0
        events_b = list(timeserie_b.raw_events())
        index_b = 0
        while index_a < len(events_a) and index_b < len(events_b):
            if events_a[index_a][0] == events_b[index_b][0]:
                result.add_value(events_a[index_a][0], events_a[index_a][1] + events_b[index_b][1])
                index_a += 1
                index_b += 1
            elif events_a[index_a][0] < events_b[index_b][0]:
                result.add_value(events_a[index_a][0], events_a[index_a][1])
                index_a += 1
            else:
                result.add_value(events_b[index_b][0], events_b[index_b][1])
                index_b += 1
        while index_a < len(events_a):
            result.add_value(events_a[index_a][0], events_a[index_a][1])
            index_a +=1
        while index_b < len(events_b):
            result.add_value(events_b[index_b][0], events_b[index_b][1])
            index_b +=1

    return result

def waterbalance_start(
    request,
    template='lizard_waterbalance/waterbalance-overview.html',
    crumbs_prepend=None):
    """Show waterbalance overview workspace.

    The workspace for the waterbalance homepage should already be present.

    Parameters:
    * crumbs_prepend -- list of breadcrumbs

    """
    if crumbs_prepend is None:
        crumbs = [{'name': 'home', 'url': '/'}]
    else:
        crumbs = list(crumbs_prepend)
    crumbs.append({'name': 'Waterbalans overzicht',
                   'title': 'Waterbalans overzicht',
                   'url': reverse('waterbalance_start')})

    special_homepage_workspace = \
        get_object_or_404(Workspace, pk=WATERBALANCE_HOMEPAGE_KEY)

    wb_configurations = retrieve_viewable_configurations(request.user)

    return render_to_response(
        template,
        {'waterbalance_configurations': wb_configurations,
         'workspaces': {'user': [special_homepage_workspace]},
         'javascript_hover_handler': 'popup_hover_handler',
         'javascript_click_handler': 'waterbalance_area_click_handler',
         'crumbs': crumbs},
        context_instance=RequestContext(request))


def waterbalance_area_summary(
    request,
    area_slug,
    scenario_slug,
    template='lizard_waterbalance/waterbalance_area_summary.html',
    crumbs_prepend=None):
    """Show the summary page of the named WaterbalanceArea.

    Parameters:
    * area -- slug of the WaterbalanceArea whose summary has to be shown
    * scenario -- slug of the WaterbalanceScenario
    * crumbs_prepend -- list of breadcrumbs

    """
    waterbalance_configuration = get_object_or_404(
         WaterbalanceConf,
         waterbalance_area__slug=area_slug,
         waterbalance_scenario__slug=scenario_slug)
    logger.debug('%s - %s' % (area_slug, scenario_slug))

    if not waterbalance_configuration.waterbalance_scenario.public and not request.user.has_perm('lizard_waterbalance.see_not_public_scenarios'):
        return HttpResponseForbidden()

    area = waterbalance_configuration.waterbalance_area

    buckets = waterbalance_configuration.open_water.buckets.filter(surface__gte=1)

    if crumbs_prepend is None:
        crumbs = [{'name': 'home', 'url': '/'}]
    else:
        crumbs = list(crumbs_prepend)
    crumbs.append({'name': 'Waterbalans overzicht',
                   'title': 'Waterbalans overzicht',
                   'url': reverse('waterbalance_start')})

    kwargs = {'area_slug': area_slug, 'scenario_slug': scenario_slug}
    crumbs.append({'name': area.name,
                   'title': area.name,
                   'url': reverse('waterbalance_area_summary', kwargs=kwargs)})

    graph_type_formitems = []
    for index, (graph_type, name) in enumerate(GRAPH_TYPES):
        formitem = {}
        formitem['id'] = 'id_graph_type_%s' % index
        formitem['value'] = graph_type
        formitem['label'] = name
        formitem['disabled'] = (graph_type not in IMPLEMENTED_GRAPH_TYPES)
        formitem['checked'] = (graph_type in INITIAL_SELECTED_GRAPH_TYPES)
        graph_type_formitems.append(formitem)
    periods = [('year', 'Per jaar', False),
               ('quarter', 'Per kwartaal', False),
               ('month', 'Per maand', True),
               ('day', 'Per dag', False)]
    # ^^^ True/False: whether it is the default radio button.  So month is.

    reset_periods = [('hydro_year', 'Hydrologisch jaar', True),
                     ('year', 'Jaar', False),
                     ('quarter', 'Kwartaal', False),
                     ('month', 'Maand', False)]

    return render_to_response(
        template,
        {'waterbalance_configuration': waterbalance_configuration,
         'buckets':buckets,
         'graph_type_formitems': graph_type_formitems,
         'periods': periods,
         'reset_periods': reset_periods,
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


def split_date_value(timeseries):
    """Return iterator with split date and time

    Aggregation function is sum.
    Optional: take average.
    """
    groupers = {'year': _first_of_year,
                'month': _first_of_month,
                'quarter': _first_of_quarter,
                'day': _first_of_day}
    grouper = groupers.get(period)
    assert grouper is not None

    for date, event in timeseries.raw_events():
        yield date, event

def get_raw_timeseries(timeseries, start, end):
    """Return the events for the given timeseries in the given range.

    Parameters:
    * timeseries -- implementation of a time series that supports a method events()
    * start -- the earliest date (and/or time) of a returned event
    * end -- the latest date (and/or time) of a returned event
    * period -- 'year', 'month' or 'day'

    """
    result =  zip(*(e for e in timeseries.raw_events()
                    if e[0] >= start and e[0] < end))
    if len(result) == 0:
        # no raw events are present but the caller expects two lists, so we
        # return two empty lists
        result = [], []
    return result


def get_cumulative_timeseries(timeseries, start, end,
                              reset_period='hydro_year', period='month',
                              multiply=1, time_shift=0):
    """Return the events for the given timeseries in the given range.

    Parameters:
    * timeseries -- implementation of a time series that supports a method events()
    * start -- the earliest date (and/or time) of a returned event
    * end -- the latest date (and/or time) of a returned event
    * period -- 'year', 'month' or 'day'

    """
    result = zip(*(e for e in cumulative_event_values(timeseries,
                                                      reset_period=reset_period,
                                                      period=period,
                                                      multiply=multiply,
                                                      time_shift=time_shift)
                   if e[0] >= start and e[0] < end))
    if len(result) == 0:
        # no cumulative events are present but the caller expects two lists, so
        # we return two empty lists
        result = [], []
    return result


def get_average_timeseries(timeseries, start, end, period='month'):
    """Return the events for the given timeseries in the given range.

    Parameters:
    * timeseries -- implementation of a time series that supports a method events()
    * start -- the earliest date (and/or time) of a returned event
    * end -- the latest date (and/or time) of a returned event
    * period -- 'year', 'month' or 'day'

    """
    result = zip(*(e for e in grouped_event_values(timeseries,
                                                   period,
                                                   average=True)
                   if e[0] >= start and e[0] < end))
    if len(result) == 0:
        # no average events are present but the caller expects two lists, so we
        # return two empty lists
        result = [], []
    return result


def get_timeseries_label(name):
    """Return the WaterbalanceLabel wth the given name.

    If no such label exists, we log the fact that nu such label exists and return
    a dummy label.

    """
    try:
        label = Label.objects.get(name__iexact=name)
    except Label.DoesNotExist:
        logger.warning("Unable to retrieve the WaterbalanceLabel '%s'", name)
        label = Label()
        label.color = "000000"
    return label


def retrieve_horizon(request):
    """Return the start and end datetime on the horizontal axis.

    The user selects the start and end date but not the date and time. This method returns
    the start date at 00:00 and the end date at 23:59:59.

    """
    start_date, end_date = current_start_end_dates(request)
    start_datetime = datetime(start_date.year,
                                       start_date.month,
                                       start_date.day,
                                       0,
                                       0,
                                       0)
    end_datetime = datetime(end_date.year,
                                     end_date.month,
                                     end_date.day,
                                     23,
                                     59,
                                     59)
    return start_datetime, end_datetime

class CacheKeyName(object):
    """Implements the creation of key names for data in the cache.

    The key name of specific data in the cache, for example the sluice error
    time series, should be different for different configurations, otherwise
    the view code would retrieve the same data from the cache for those
    configurations.

    Instance variables:
      * configuration_slug *
        the string that will be appended to each cache key name

    The configuration slug is used to create cache key names that differ for
    different configurations.

    """

    def __init__(self, configuration):
        """Set the configuration_slug instance variable.

        The configuration_slug is created from the return value of a call to
        the __unicode__ method of the configuration.

        """
        self.configuration_slug = slugify(configuration.__unicode__())

    def get(self, name):
        """Return a key name for one configuration based on the given name.

        """
        return name + "::" + self.configuration_slug

class CachedWaterbalanceComputer(WaterbalanceComputer2):
    """Wraps subclasses given WaterbalanceComputer and caches its results.

    A CachedWaterbalanceComputer reimplements those WaterbalanceComputer
    methods that are used in this module. Each reimplemented method checks
    whether the requested results of the parent method are already present in
    the Django cache. If these results are present, the reimplemented method
    retrieves and returns them to the caller. If the results are not present,
    each reimplemented method calls the parent method, stores the results in
    the cache and then returns them to the caller.

    This class takes some care to be able to use memcached as a backend. By
    default, memcached can only store objects that are up to 1 MB in size. For
    our test case this meant that the results of the call to
    WaterbalanceComputer.get_fraction_timeseries did not fit in the
    cache. Therefore, the reimplementation of this method stores the results in
    two separate objects.

    Note that if specific data cannot be stored in the cache, the view still
    functions but it will take longer to display the graphs. The data not in
    the cache will have to be recalculated each time it is requested.

    Instance variables:
      *cache_key_name*
        a CacheKeyName to create the key names for data in the cache

    """
    def __init__(self, *args, **kwargs):
        """Set the CacheKeyName to create the key names for data in the cache.

        The first non-keyword argument should be the CacheKeyName to set.

        """
        assert len(args) > 1
        self.cache_key_name = args[0]

        super(CachedWaterbalanceComputer, self).__init__(*args[1:], **kwargs)

    def get_cached_data(self, name):
        """Return the data from the cache using a key based on the given name.

        This method uses self.cache_key_name to retrieve the right key name for
        the current configuration.

        """
        key_name = self.cache_key_name.get(name)
        return cache.get(key_name)

    def set_cached_data(self, name, data):
        """Store the data in the cache using a key based on the given name.

        This method uses self.cache_key_name to retrieve the right key for
        the current configuration.

        """
        key_name = self.cache_key_name.get(name)
        cache.set(key_name, data, 24 * 60 * 60)

    def calc_sluice_error_timeseries(self, start_date, end_date):

        sluice_error = self.get_cached_data("sluice_error")
        if sluice_error is None:

            parent = super(CachedWaterbalanceComputer, self)
            sluice_error = \
                parent.calc_sluice_error_timeseries(start_date,
                                                    end_date)

            self.set_cached_data("sluice_error", sluice_error)

        return sluice_error

    def get_open_water_incoming_flows(self,
                                      start_date,
                                      end_date):

        incoming = self.get_cached_data("incoming")
        if incoming is None:

            parent = super(CachedWaterbalanceComputer, self)
            incoming = parent.get_open_water_incoming_flows(start_date,
                                                            end_date)
            self.set_cached_data("incoming", incoming)

        return incoming

    def get_open_water_outgoing_flows(self,
                                      start_date,
                                      end_date):

        outgoing = self.get_cached_data("outgoing")
        if outgoing is None:

            parent = super(CachedWaterbalanceComputer, self)
            outgoing = parent.get_open_water_outgoing_flows(start_date,
                                                            end_date)
            self.set_cached_data("outgoing", outgoing)

        return outgoing

    def get_level_control_timeseries(self, start_date, end_date):

        outcome = self.get_cached_data("outcome")
        if outcome is None:

            parent = super(CachedWaterbalanceComputer, self)
            outcome = parent.get_level_control_timeseries(start_date,
                                                          end_date)
            self.set_cached_data("outcome", outcome)

        return outcome

    def get_level_control_pumping_stations(self):

        pair = self.get_cached_data("pair")
        if pair is None:

            parent = super(CachedWaterbalanceComputer, self)
            pair = parent.get_level_control_pumping_stations()
            self.set_cached_data("pair", pair)

        return pair

    def get_reference_timeseries(self, start_date, end_date):

        ref_in = self.get_cached_data("ref_in")
        ref_out = self.get_cached_data("ref_out")
        if ref_in is None or ref_out is None:

            parent = super(CachedWaterbalanceComputer, self)
            ref_in, ref_out = parent.get_reference_timeseries(start_date,
                                                              end_date)
            self.set_cached_data("ref_in", ref_in)
            self.set_cached_data("ref_out", ref_out)

        return ref_in, ref_out

    def get_waterlevel_with_sluice_error(self, start_date, end_date):

        waterlevel = self.get_cached_data("waterlevel")
        sluice_error = self.get_cached_data("sluice_error")
        if waterlevel is None or sluice_error is None:
            parent = super(CachedWaterbalanceComputer, self)
            waterlevel, sluice_error = parent.get_waterlevel_with_sluice_error(
                start_date, end_date)
            self.set_cached_data("waterlevel", waterlevel)
            self.set_cached_data("sluice_error", sluice_error)
        return waterlevel, sluice_error

    def get_fraction_timeseries(self, start_date, end_date):

        fractions_1 = self.get_cached_data("fractions_1")
        fractions_2 = self.get_cached_data("fractions_2")
        if fractions_1 is None or fractions_2 is None:

            parent = super(CachedWaterbalanceComputer, self)
            fractions = parent.get_fraction_timeseries(start_date,
                                                       end_date)

            # When we use memcached as the backend, the default maximum size
            # for a single object in the cache is 1 MB. It turned out that the
            # fractions dictionary could easily exceed that limit. For that
            # reason we partition the fractions in two dictionaries and store
            # each part separately.
            fractions_1 = {}
            fractions_2 = {}
            key_count = 0
            for key, values in fractions.iteritems():
                if key_count < 4:
                    fractions_1[key] = values
                else:
                    fractions_2[key] = values
                key_count = key_count + 1

            self.set_cached_data("fractions_1", fractions_1)
            self.set_cached_data("fractions_2", fractions_2)

        fractions = fractions_1
        for key, values in fractions_2.iteritems():
            fractions[key] = values

        return fractions

    def get_concentration_timeseries(self, start_date, end_date):

        concentrations = self.get_cached_data("concentrations")
        if concentrations is None:

            parent = super(CachedWaterbalanceComputer, self)
            concentrations = parent.get_concentration_timeseries(start_date,
                                                                 end_date)
            self.set_cached_data("concentrations", concentrations)

        return concentrations

    def get_impact_timeseries(self, start_date, end_date):

        impact = self.get_cached_data("impact")
        impact_incremental = self.get_cached_data("impact_incremental")
        if impact is None or impact_incremental is None:

            parent = super(CachedWaterbalanceComputer, self)
            impact, impact_incremental = parent.get_impact_timeseries(
                start_date, end_date)
            self.set_cached_data("impact", impact)
            self.set_cached_data("impact_incremental", impact_incremental)

        return impact, impact_incremental


# @profile("waterbalance_area_graph.prof")
def waterbalance_area_graph(
    configuration,
    waterbalance_computer,
    start_date,
    end_date,
    period,
    width, height):
    """Draw the graph for the given area and of the given type.

    area_slug: i.e. artsveldsche-polder-oost
    period: i.e. 'month'
    start_date, end_date: start and end_date for graph
    start_datetime, end_datetime: start and enddate for calculation
    width, height: width and height of output image
    """
    calc_start_datetime, calc_end_datetime = \
        configuration.get_calc_period(date2datetime(end_date))

    graph = Graph(start_date, end_date, width, height)
    graph.suptitle("Waterbalans [m3]")
    bar_width = BAR_WIDTH[period]

    t1 = time()

    labels = dict([(label.program_name, label) for
                   label in Label.objects.all()])

    #collect all data
    incoming = waterbalance_computer.get_open_water_incoming_flows(
        calc_start_datetime,
        calc_end_datetime)
    sluice_error = \
        waterbalance_computer.calc_sluice_error_timeseries(calc_start_datetime,
                                                           calc_end_datetime)
    outgoing = waterbalance_computer.get_open_water_outgoing_flows(
        calc_start_datetime, calc_end_datetime)

    #define bars, without sluice error
    incoming_bars = []
    incoming_bars += [(labels["hardened"].name, incoming["hardened"], labels['hardened'], "discharge_hardened"),
                     (labels["drained"].name, incoming["drained"], labels['drained'], "discharge_drained"),
                     (labels["flow_off"].name, incoming["flow_off"], labels['flow_off'], "discharge_flow_off"),
                     (labels["undrained"].name, incoming["undrained"], labels['undrained'], "discharge_drainage"),
                     (labels["precipitation"].name, incoming["precipitation"], labels['precipitation'], "precipitation"),
                     (labels["seepage"].name, incoming["seepage"], labels['seepage'], "seepage")]

    incoming_bars += [
        (structure.name, timeserie, structure.label, "discharge_" + structure.name) for structure, timeserie in
        incoming['defined_input'].items()]

    outgoing_bars = []
    outgoing_bars = [
        (labels["indraft"].name, outgoing["indraft"], labels['indraft'], "indraft"),
        (labels["evaporation"].name, outgoing["evaporation"], labels['evaporation'], "evaporation"),
        (labels["infiltration"].name, outgoing["infiltration"], labels['infiltration'], "infiltration")
         ]

    outgoing_bars += [(structure.name, timeserie, structure.label, "discharge_" + structure.name) for structure, timeserie in outgoing['defined_output'].items()]

    #sort
    incoming_bars = sorted(incoming_bars, key=lambda bar:-bar[2].order)
    outgoing_bars = sorted(outgoing_bars, key=lambda bar: bar[2].order)

    #define legend
    names = ["sluitfout t.o.v. gemaal"] + [abridged_legend_name(bar[0]) for bar in incoming_bars + outgoing_bars]
    colors = [labels['sluice_error'].color] + [bar[2].color for bar in incoming_bars + outgoing_bars]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]
    graph.legend_space()
    graph.legend(handles, names)
    incoming_bars.reverse()

    #send bars to graph
    top_height_in = TopHeight()
    top_height_out = TopHeight()

    dict_series = {}
    for bars, top_height in [(incoming_bars, top_height_in), \
                             (outgoing_bars, top_height_out)]:
        for bar in bars:
            label = bar[2]
            times, values = get_average_timeseries(bar[1],
                                                   date2datetime(start_date),
                                                   date2datetime(end_date),
                                                   period=period)
            dict_series[bar[3]] = bar[1]
            # add the following keyword argument to give the bar edges the same
            # color as the bar itself: edgecolor='#' + label.color
            color = label.color
            bottom = top_height.get_heights(times)
            graph.axes.bar(times, values, bar_width, color=color,
                           edgecolor=color, bottom=bottom)
            top_height.stack_bars(times, values)

    #sluice error
    label = labels['sluice_error']
    times, values = get_average_timeseries(sluice_error,
                                           date2datetime(start_date),
                                           date2datetime(end_date),
                                           period=period)

    # dict_series["sluice_error"] = sluice_error
    # write_to_pi_file(location_id = "SAP", filename="waterbalance-graph.xml", timeseries=dict_series)

    positive_times = []
    positive_sluice_error = []
    negative_times = []
    negative_sluice_error = []
    for timestamp, value in zip(times, values):
        # logger.debug("%s, %f", timestamp.isoformat(), value)
        if value > 0:
            positive_times.append(timestamp)
            positive_sluice_error.append(value)
        else:
            negative_times.append(timestamp)
            negative_sluice_error.append(value)

    color = label.color

    #first incoming sluice_error
    bottom = top_height_in.get_heights(positive_times)
    graph.axes.bar(positive_times, positive_sluice_error, bar_width, color=color,
                   edgecolor=color, bottom=bottom)
    top_height_in.stack_bars(positive_times, positive_sluice_error)

    #next outgoing sluice_error
    bottom = top_height_out.get_heights(negative_times)
    graph.axes.bar(negative_times, negative_sluice_error, bar_width, color=color,
                   edgecolor=color, bottom=bottom)
    top_height_out.stack_bars(negative_times, negative_sluice_error)

    logger.debug("Grabbing all graph data took %s seconds.", time() - t1)
    return graph

def waterbalance_water_level(configuration,
                             waterbalance_computer,
                             start_date,
                             end_date,
                             period,
                             reset_period,
                             width, height,
                             with_sluice_error=False):
    """Draw the graph for the given area en scenario and of the given type."""
    calc_start_datetime, calc_end_datetime = \
                         configuration.get_calc_period(date2datetime(end_date))

    graph = Graph(start_date, end_date, width, height)
    if with_sluice_error:
        title = "Waterpeil met sluitfout [m NAP]"
    else:
        title = "Waterpeil [m NAP]"
    graph.suptitle(title)

    t1 = time()

    labels = dict([(l.program_name, l) for l in Label.objects.all()])

    #define bars
    bars = []
    #gemeten waterpeilen
    for tijdserie in configuration.references.filter(parameter__sourcetype=Parameter.TYPE_MEASURED, parameter__parameter=Parameter.PARAMETER_WATERLEVEL):
        bars.append((tijdserie.name, tijdserie.get_timeseries(), labels['meas_waterlevel']))

    bars.append(("waterpeilen",
                 waterbalance_computer.get_level_control_timeseries(calc_start_datetime,
                                                                    calc_end_datetime)['water_level'],
                labels['calc_waterlevel']))

    if reset_period == 'hydro_year' and period == 'year':
        # This is a really strange combination for which the rest of this
        # function is not suited. We fix that as follows.
        period = 'hydro_year'
    # When the reset period is smaller than the group period, it is possible
    # that the grouper returns a date before the date of the resetter, for
    # example when the reset period is a month and the group period a
    # quarter. But to which cumulative time series should this lead?
    #
    # To "fix" this problem, we use the following rule:
    #
    #    When the reset period is smaller than the group period, use the reset
    #    period also for the group period.
    #
    # In this way, the user always sees the reset.
    keys = ['day', 'month', 'quarter', 'hydro_year', 'year']
    if keys.index(reset_period) < keys.index(period):
        period = reset_period

    # Add sluice error to bars.
    if with_sluice_error:
        waterlevel, sluice_error = waterbalance_computer.get_waterlevel_with_sluice_error(calc_start_datetime,
                                                                                          calc_end_datetime)

        times, values = get_cumulative_timeseries(sluice_error,
                                                  calc_start_datetime,
                                                  calc_end_datetime,
                                                  reset_period=reset_period,
                                                  period='day')
        # We have computed the cumulative sluice error in [m3/day], however we
        # will display it as a difference in water level, so [m/day]. We make
        # that translation here.
        surface = 1.0 * configuration.open_water.surface
        cumulative_sluice_error = TimeseriesStub()
        for date, cumulative_value in zip(times, values):
            value = cumulative_value / surface
            cumulative_sluice_error.add_value(date, value)

        sluice_error_waterlevel = add_timeseries(waterlevel, cumulative_sluice_error)

        bars.append(("waterpeilen, met sluitfout", sluice_error_waterlevel,
                     labels['sluice_error']))

    names = [abridged_legend_name(bar[2].name) for bar in bars]
    colors = [bar[2].color for bar in bars]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    graph.legend_space()
    graph.legend(handles, names)

    for bar in bars:
        label = bar[2]
        if bar[0] == "waterpeilen, met sluitfout":
            times, values = get_timeseries(bar[1],
                                           calc_start_datetime,
                                           calc_end_datetime,
                                           period='day')
        else:
            times, values = get_average_timeseries(
                bar[1], date2datetime(start_date),
                date2datetime(end_date), period=period)

        color = label.color
        graph.axes.plot(times, values, color=color)

    logger.debug("Grabbing all graph data took %s seconds.", time() - t1)
    return graph

def waterbalance_cum_discharges(configuration,
                             waterbalance_computer,
                             start_date,
                             end_date,
                             period,
                             reset_period,
                             width, height):
    """Draw the graph for the given area en scenario and of the given type."""
    calc_start_datetime, calc_end_datetime = configuration.get_calc_period(date2datetime(end_date))

    graph = Graph(start_date, end_date, width, height)
    graph.suptitle("Cumulatieve debieten")

    t1 = time()

    labels = dict([(label.program_name, label) for label in Label.objects.all()])

    bars_in = []
    bars_out = []
    line_in = []
    line_out = []
    #verzamel gegevens
    control = waterbalance_computer.get_level_control_timeseries(
                                    calc_start_datetime,
                                    calc_end_datetime)

    intake, pump = waterbalance_computer.get_level_control_pumping_stations()
    if intake is not None:
        line_in.append((extended_legend_name(intake.name, " (berekend)"),
                        control['intake_wl_control'],
                        labels['intake_wl_control'], '#000000'))
    if pump is not None:
        line_out.append((extended_legend_name(pump.name, " (berekend)"),
                         control['outtake_wl_control'],
                         labels['outtake_wl_control'], '#000000'))

    ref_in, ref_out = waterbalance_computer.get_reference_timeseries(
                                    calc_start_datetime,
                                    calc_end_datetime)
    nr = 0
    for structure in ref_out:
        for pump_line in structure.pump_lines.all():
            bars_out.append((pump_line.name, pump_line.retrieve_timeseries(), structure.label, colors_list[nr]))
            nr += 1
    for structure in ref_in:
        for pump_line in structure.pump_lines.all():
            bars_in.append((pump_line.name, pump_line.retrieve_timeseries(), structure.label, colors_list[nr]))
            nr += 1

    names = [abridged_legend_name(bar[0]) for bar in bars_out + bars_in]
    colors = [bar[3] for bar in bars_out + bars_in ]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    names += [bar[0] for bar in line_out + line_in]
    colors_line = [bar[3] for bar in line_out + line_in]
    handles += [Line2D([], [], color=color, lw=2) for color in colors_line]

    graph.legend_space()
    graph.legend(handles, names)

    if reset_period == 'hydro_year' and period == 'year':
        # This is a really strange combination for which the rest of this
        # function is not suited. We fix that as follows.
        period = 'hydro_year'

    # When the reset period is smaller than the group period, it is possible
    # that the grouper returns a date before the date of the resetter, for
    # example when the reset period is a month and the group period a
    # quarter. But to which cumulative time series should this lead?
    #
    # To "fix" this problem, we use the following rule:
    #
    #    When the reset period is smaller than the group period, use the reset
    #    period also for the group period.
    #
    # In this way, the user always sees the reset.

    keys = ['day', 'month', 'quarter', 'hydro_year', 'year']
    if keys.index(reset_period) < keys.index(period):
        period = reset_period

    bar_width = BAR_WIDTH[period]

    top_height_in = TopHeight()
    top_height_out = TopHeight()
    for bars, top_height in [(bars_in, top_height_in), (bars_out, top_height_out)]:
        for bar in bars:
            label = bar[2]

            # Note that we have to compute the cumulative values for the
            # complete time range. Should we only compute the cumulative values
            # for the time range on the time axis of the graph, the cumulative
            # values would start with the wrong value.
            times, values = get_cumulative_timeseries(bar[1],
                calc_start_datetime, calc_end_datetime,
                period=period, reset_period=reset_period, multiply= -1)

            color = bar[3]
            bottom = top_height.get_heights(times)
            graph.axes.bar(times, values, bar_width, color=color, edgecolor=color,
                               bottom=bottom)
            top_height.stack_bars(times, values)

    for bars in [line_in, line_out]:
        for bar in bars:
            label = bar[2]

            # Note that we have to compute the cumulative values for the
            # complete time range. Should we only compute the cumulative values
            # for the time range on the time axis of the graph, the cumulative
            # values would start with the wrong value.
            times, values = get_cumulative_timeseries( bar[1],
                calc_start_datetime, calc_end_datetime,
                period=period, reset_period=reset_period)

            # The cumulative events (times, values) do not correspond to the
            # data points in the graph. For example, the date of each event is
            # the first day of each period but as the events contain cumulative
            # values, they should be drawn at the end of each period. The
            # following snippet of code prepares the data for drawing.
            data = DataForCumulativeGraph(times, values)
            times, values = data.retrieve_for_drawing(period, reset_period)

            color = bar[3]
            graph.axes.plot(times, values, color=color, lw=2)

    logger.debug("Grabbing all graph data took %s seconds.", time() - t1)
    return graph

#@profile("waterbalance_fraction_distribution.prof")
def waterbalance_fraction_distribution(
            configuration, waterbalance_computer, start_date, end_date,
            period, width, height, concentration=Parameter.PARAMETER_CHLORIDE):
    """Draw the graph for the given area and of the given type."""
    calc_start_datetime, calc_end_datetime = configuration.get_calc_period(date2datetime(end_date))

    graph = Graph(start_date, end_date, width, height)

    # Add second axes.
    graph.init_second_axes()

    if concentration == Parameter.PARAMETER_CHLORIDE:
        substance = "chloride"
    else:
        substance = "fosfaat"
    title = "Fractieverdeling en %s" % substance
    graph.suptitle(title)
    bar_width = BAR_WIDTH[period]

    t1 = time()

    labels = dict([(label.program_name, label) for label in Label.objects.all()])

    #get data and bars
    fractions = waterbalance_computer.get_fraction_timeseries(
        calc_start_datetime, calc_end_datetime)

    bars = [(labels['initial'].name, fractions["initial"], labels['initial']),
            (labels['precipitation'].name, fractions["precipitation"], labels['precipitation']),
            (labels['seepage'].name, fractions["seepage"], labels['seepage']),
            (labels['hardened'].name, fractions["hardened"], labels['hardened']),
            (labels['drained'].name, fractions["drained"], labels['drained']),
            (labels['undrained'].name, fractions["undrained"], labels['undrained']),
            (labels['flow_off'].name, fractions["flow_off"], labels['flow_off'])]

    for key, timeserie in fractions['intakes'].items():
        bars.append((key.name, timeserie, key.label))

    #sort
    bars = sorted(bars, key=lambda bar:-bar[2].order)

    #setup legend
    names = [abridged_legend_name(bar[0]) for bar in bars]
    colors = [bar[2].color for bar in bars]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    bars.reverse()
    # Now draw the graph
    times = []
    values = []
    top_height = TopHeight()
    for bar in bars:
        label = bar[2]
        times, values = get_average_timeseries(
            bar[1], date2datetime(start_date), date2datetime(end_date),
            period=period)

        # add the following keyword argument to give the bar edges the same
        # color as the bar itself: edgecolor='#' + label.color

        color = label.color
        bottom = top_height.get_heights(times)
        graph.axes.bar(times, values, bar_width, color=color, edgecolor=color,
                       bottom=bottom)
        top_height.stack_bars(times, values)

    # Draw axis 2
    # show the computed substance levels
    substance_timeseries = waterbalance_computer.get_concentration_timeseries(date2datetime(calc_start_datetime), date2datetime(calc_end_datetime))

    style = dict(color='black', lw=3)
    handles.append(Line2D([], [], **style))
    names.append(extended_legend_name(substance, " berekend"))

    times, values = get_average_timeseries(
            substance_timeseries, date2datetime(start_date), date2datetime(end_date),
            period=period)

    graph.ax2.plot(times, values, **style)

    #add metingen
    if concentration == Parameter.PARAMETER_CHLORIDE:
         parameter = Parameter.PARAMETER_CHLORIDE
    else:
         parameter = Parameter.PARAMETER_FOSFAAT

    nr = 0
    for tijdserie in configuration.references.filter(parameter__parameter=parameter, parameter__sourcetype=Parameter.TYPE_MEASURED):
        style = dict(color=colors_list[nr], markersize=10, marker='d', linestyle=" ")
        nr += 1
        times, values = get_raw_timeseries(tijdserie.get_timeseries(),
                                            date2datetime(start_date),
                                            date2datetime(end_date))
        graph.ax2.plot(times, values, **style)
        handles.append(Line2D([], [], **style))
        names.append(extended_legend_name(tijdserie.name, " gemeten"))

    graph.legend_space()
    graph.legend(handles, names)

    graph.axes.set_ylim(0, 100)
    graph.ax2.set_ylim(ymin=0)

    logger.debug("Grabbing all graph data took %s seconds.", time() - t1)
    return graph


class LegendInfo(object):
    """Implements the retrieval of the legend information of each flow.

    See the doc string of method 'retrieve' for more information.

    """

    def retrieve_labels(self):
        """Retrieve the label information from the database.

        """
        labels = Label.objects.all()
        self.labels = dict([(l.program_name, (l.name, l)) for l in labels])

    def retrieve(self, key):
        """Return the tuple (legend name, Label) for the given key.

        The key is either a string or a PumpingStation. When it is a string,
        the string is the program name of a Label l and this method returns the
        tuple (l.name, l). When it is a PumpingStation p, this method returns
        the tuple (t.name, t.label).

        """
        if isinstance(key, PumpingStation):
            label_name, label = key.name, key.label
        else:
            label_name, label = self.labels[key]

        return label_name, label


def waterbalance_phosphate_impact(
           configuration, waterbalance_computer, start_date, end_date,
            period, width, height):
    """Draw the graph for the given area and of the given type."""
    calc_start_datetime, calc_end_datetime = configuration.get_calc_period(date2datetime(end_date))

    graph = Graph(start_date, end_date, width, height)
    graph.suptitle("Fosfaatbelasting [mg/m2/dag]")

    bar_width = BAR_WIDTH[period]

    t1 = time()

    #get data and bars
    impacts, impacts_incremental = waterbalance_computer.get_impact_timeseries(calc_start_datetime,
                                                                               calc_end_datetime)

    bars_minimum = []
    bars_increment = []
    legend = []

    legend_info = LegendInfo()
    legend_info.retrieve_labels()

    for index, impact in enumerate(impacts):
        label_name, label = legend_info.retrieve(impact.label)
        name = extended_legend_name(label_name, " (min)")
        name_incremental = extended_legend_name(label_name, " (incr)")

        bars_minimum.append((name,
                     impact.timeseries,
                     label,
                     label.color))
        bars_increment.append((name_incremental,
                               impacts_incremental[index].timeseries,
                               label,
                               label.color_increment))
        legend.append((label.order, name, label.color))
        legend.append((label.order + 1000, name_incremental, label.color_increment))

    logger.debug('1: Got bars in %s seconds' %
                 (time() - t1))

    legend = sorted(legend, key=lambda bar:-bar[0])

    names = [abridged_legend_name(line[1]) for line in legend]
    colors = [line[2] for line in legend]
    handles = [Line2D([], [], color=color, lw=4) for color in colors]

    graph.legend_space()
    graph.legend(handles, names)

    bars_minimum = sorted(bars_minimum, key=lambda bar:bar[2].order)
    bars_increment = sorted(bars_increment, key=lambda bar:bar[2].order)

    top_height = TopHeight()

    for bars in [bars_minimum, bars_increment]:
        for bar in bars:
            # Label is the min name or the incr name
            label = bar[2]
            times, values = get_average_timeseries(bar[1],
                                                   date2datetime(start_date),
                                                   date2datetime(end_date),
                                                   period=period)

            color = bar[3]
            bottom = top_height.get_heights(times)
            graph.axes.bar(
                times, values, bar_width, color=color, edgecolor=color,
                bottom=bottom)
            top_height.stack_bars(times, values)

    logger.debug('1: Got axes in %s seconds' %
                 (time() - t1))

    return graph


def waterbalance_area_graphs(request,
                             area_slug,
                             scenario_slug,
                             graph_type=None):
    """
    Return area graph.

    """
    configuration = WaterbalanceConf.objects.get(
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    area = Area(configuration)
    waterbalance_computer = \
        CachedWaterbalanceComputer(CacheKeyName(configuration), configuration,
                                   area)

    period = request.GET.get('period', 'month')
    reset_period = request.GET.get('reset_period', 'year')
    #start_datetime, end_datetime = retrieve_horizon(request)
    #start_date = start_datetime.date()
    #end_date = end_datetime.date() + timedelta(1)

    # Don't know the difference in above start/end dates. This seems
    # better, but not sure if it works correctly with existing
    # functions.
    start_date, end_date = current_start_end_dates(request)

    width = request.GET.get('width', 1600)
    height = request.GET.get('height', 400)

    if graph_type == 'waterbalans':
        graph = waterbalance_area_graph(
            configuration, waterbalance_computer, start_date, end_date,
            period, width, height)
    elif graph_type == 'waterpeil':
        graph = waterbalance_water_level(
            configuration, waterbalance_computer, start_date, end_date,
            period, reset_period, width, height)
    elif graph_type == 'waterpeil_met_sluitfout':
        graph = waterbalance_water_level(
            configuration, waterbalance_computer, start_date, end_date,
            period, reset_period, width, height, with_sluice_error=True)
    elif graph_type == 'fracties_chloride':
        graph = waterbalance_fraction_distribution(
            configuration, waterbalance_computer, start_date, end_date,
            period, width, height, Parameter.PARAMETER_CHLORIDE)
    elif graph_type == 'cumulatief_debiet':
        graph = waterbalance_cum_discharges(
            configuration, waterbalance_computer, start_date, end_date,
            period, reset_period, width, height)
    elif graph_type == 'fosfaatbelasting':
        graph = waterbalance_phosphate_impact(
           configuration, waterbalance_computer, start_date, end_date,
            period, width, height)

    #graph.add_today()

    #canvas = FigureCanvas(graph.figure)
    #response = HttpResponse(content_type='image/png')

    response = graph.http_png()
    response['Cache-Control'] = 'max-age=600'
    #canvas.print_png(response)

    return response


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
    if request.is_ajax():
        area_slug = request.POST['area_slug']
        scenario_slug = request.POST['scenario_slug']
        selected_graph_types = request.POST.getlist('graphs')
        period = request.POST['period']
        reset_period = request.POST['reset_period']

        graphs = []
        for graph_type, name in GRAPH_TYPES:
            if not graph_type in selected_graph_types:
                continue

            url = (reverse('waterbalance_area_graph',
                           kwargs={'area_slug': area_slug,
                                   'scenario_slug': scenario_slug,
                                   'graph_type': graph_type}) +
                   '?period=' + period +
                   '&reset_period=' + reset_period)
            graphs.append(url)
        json = simplejson.dumps(graphs)

        # If the data has not been cached, we make sure we compute and cache it
        # now, otherwise all graphs start a computation on their own.

        configuration = WaterbalanceConf.objects.get(
            waterbalance_area__slug=area_slug,
            waterbalance_scenario__slug=scenario_slug)

        cache_key_name = CacheKeyName(configuration)
        area = Area(configuration)
        waterbalance_computer = CachedWaterbalanceComputer(cache_key_name,
                                                           configuration,
                                                           area)

        if waterbalance_computer.get_cached_data("sluice_error") is None:
            calc_start_datetime, calc_end_datetime = \
                configuration.get_calc_period()
            waterbalance_computer.compute(calc_start_datetime,
                                          calc_end_datetime)

        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponse("Should not be run this way.")


def search_fews_lkeys(request):
    if request.is_ajax():
        pkey = request.POST['pkey']
        fkey = request.POST['fkey']
        timeseries = Timeserie.objects.filter(parameterkey=pkey, filterkey=fkey)
        timeseries = timeseries.distinct().order_by("locationkey")
        lkeys = [(ts.locationkey.lkey, create_location_label(ts.locationkey)) for ts in timeseries]
        lkeys.sort(key=lambda pair: pair[1])
        json = simplejson.dumps(lkeys)
        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponse("Should not be run this way.")


def _actual_recalculation(request, area_slug, scenario_slug):
    """ old function

    Recalculate graph data by emptying the cache: used by two views."""
    start_datetime, end_datetime = retrieve_horizon(request)

    conf = WaterbalanceConf.objects.get(
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)

    waterbalance_graph_data(conf, start_datetime, end_datetime,
                            recalculate=True)


def recalculate_graph_data(request, area_slug=None, scenario_slug=None):
    """Recalculate the graph data and store the data in the cache."""
    if request.method == "POST":

        configuration = WaterbalanceConf.objects.get(
             waterbalance_area__slug=area_slug,
             waterbalance_scenario__slug=scenario_slug)

        cache_key_name = CacheKeyName(configuration)
        names = [ "sluice_error", "total_outtakes", "incoming", "outgoing",
            "outcome", "pair", "ref_in", "ref_out", "sluice_error_waterlevel",
            "fractions_1", "fractions_2", "concentrations", "impact",
            "impact_incremental" ]
        key_names = [cache_key_name.get(name) for name in names]
        cache.delete_many(key_names)
        area = Area(configuration)
        waterbalance_computer = \
                              CachedWaterbalanceComputer(cache_key_name,
                                                         configuration,
                                                         area)
        calc_start_datetime, calc_end_datetime = configuration.get_calc_period()
        waterbalance_computer.compute(calc_start_datetime, calc_end_datetime)

        return HttpResponseRedirect(
            reverse(
                'waterbalance_area_summary',
                kwargs={'area_slug': area_slug,
                        'scenario_slug': scenario_slug}))
    else:
        return HttpResponse("false")


def waterbalance_area_edit(request,
                           area_slug=None,
                           template='lizard_waterbalance/waterbalance_area_edit.html',
                           crumbs_prepend=None):
    """Show the edit page of the named WaterbalanceArea.

    Injected with ajax into the waterbalance_area_summary page.

    Parameters:
    * area -- name of the WaterbalanceArea whose summary has to be shown
    * crumbs_prepend -- list of breadcrumbs

    """
    return render_to_response(
        template,
        {'area': area_slug,
         },
        context_instance=RequestContext(request))


def _sub_multiple(request,
                  instances=None,
                  template=None,
                  field_names=None,
                  header_name=None,
                  form_class=None,
                  form_url=None):
    """
    Generic sub multiple screen (?)

    instance is a model object
    """
    if template is None:
        template = 'lizard_waterbalance/waterbalance_area_edit_multiple.html'
    header = []
    lines = []
    if instances:
        instance = instances[0]
        header_item = {}
        header_item['name'] = instance._meta.get_field(header_name).verbose_name.capitalize()
        header.append(header_item)
        for field_name in field_names:
            line = {}
            field = instance._meta.get_field(field_name)
            row_header = {}
            row_header['name'] = field.verbose_name.capitalize()
            row_header['title'] = field.help_text
            line['header'] = row_header
            line['items'] = []
            lines.append(line)

    for instance in instances:
        header_item = {}
        header_item['name'] = getattr(instance, header_name).capitalize()
        if form_url:
            header_item['edit_url'] = form_url + str(instance.id) + '/'
        header.append(header_item)
        for index, field_name in enumerate(field_names):
            line = lines[index]
            item = {}
            item['value'] = getattr(instance, field_name)
            if field_name in TRUE_FALSE_EXCEPTIONS:
                if isinstance(item['value'], bool):
                    if item['value']:
                        item['value'] = TRUE_FALSE_EXCEPTIONS[field_name][0]
                    else:
                        item['value'] = TRUE_FALSE_EXCEPTIONS[field_name][1]
            line['items'].append(item)


    return render_to_response(
        template,
        {'header': header,
         'lines': lines,
         },
        context_instance=RequestContext(request))


def _sub_edit(request,
              area_slug,
              scenario_slug,
              instance=None,
              template=None,
              fixed_field_names=None,
              form_class=None,
              form_url=None,
              previous_url=None):
    """
    Generic sub edit screen (?)
    """
    if template is None:
        template = 'lizard_waterbalance/waterbalance_area_edit_sub.html'
    fixed_items = []
    for fixed_field_name in fixed_field_names:
        field = instance._meta.get_field(fixed_field_name)
        fixed_items.append(dict(
                name=field.verbose_name.capitalize(),
                title=field.help_text,
                value=getattr(instance, fixed_field_name)))
    form = None
    if form_class is not None:
        if request.method == 'POST':
            form = form_class(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                _actual_recalculation(request, area_slug, scenario_slug)
                messages.success(
                    request,
                    u"Gegevens zijn opgeslagen en de grafiek is herberekend.")
        else:
            form = form_class(instance=instance)

    return render_to_response(
        template,
        {'fixed_items': fixed_items,
         'form': form,
         'form_url': form_url,
         'previous_url': previous_url,
         },
        context_instance=RequestContext(request))


def waterbalance_area_edit_sub_conf(request,
                                    area_slug,
                                    scenario_slug,
                                    template=None):
    instance = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    fixed_field_names = []  # ['name']
    form_class = WaterbalanceConfEditForm
    form_url = reverse('waterbalance_area_edit_sub_conf',
                       kwargs={'area': area_slug, 'scenario': scenario_slug})
    return _sub_edit(request,
                     area_slug=area_slug,
                     scenario_slug=scenario_slug,
                     instance=instance,
                     template=template,
                     fixed_field_names=fixed_field_names,
                     form_class=form_class,
                     form_url=form_url,
                     )


def waterbalance_area_edit_sub_openwater(request,
                                         area_slug,
                                         scenario_slug,
                                         template=None):
    conf = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    instance = conf.open_water
    fixed_field_names = ['name']
    form_class = OpenWaterEditForm
    form_url = reverse(
        'waterbalance_area_edit_sub_openwater',
        kwargs={'area_slug': area_slug, 'scenario_slug': scenario_slug})
    return _sub_edit(request,
                     area_slug=area_slug,
                     scenario_slug=scenario_slug,
                     instance=instance,
                     template=template,
                     fixed_field_names=fixed_field_names,
                     form_class=form_class,
                     form_url=form_url,
                     )

def waterbalance_area_edit_sub_buckets(request,
                                       area_slug,
                                       scenario_slug,
                                       template=None):
    conf = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    instance = conf.open_water
    fixed_field_names = []
    return _sub_edit(request,
                     area_slug=area_slug,
                     scenario_slug=scenario_slug,
                     instance=instance,
                     template=template,
                     fixed_field_names=fixed_field_names,
                     )


def waterbalance_area_edit_sub_out(request,
                                   area_slug,
                                   scenario_slug,
                                   template=None):
    """Posten uit."""
    conf = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    instances = [ps for ps in conf.open_water.pumping_stations.all()
                 if not ps.into]

    header_name = 'name'
    field_names = ['percentage',
                   'computed_level_control',
                   ]
    return _sub_multiple(request,
                         instances=instances,
                         template=template,
                         field_names=field_names,
                         header_name=header_name,
                         )


def waterbalance_area_edit_sub_in(request,
                                  area_slug,
                                  scenario_slug,
                                  template=None):
    conf = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    instances = [ps for ps in conf.open_water.pumping_stations.all()
                 if ps.into]

    header_name = 'name'
    field_names = ['percentage',
                   'computed_level_control',
                   ]
    form_url = reverse(
        'waterbalance_area_edit_sub_in',
        kwargs={'area_slug': area_slug, 'scenario_slug': scenario_slug})

    return _sub_multiple(request,
                         instances=instances,
                         template=template,
                         field_names=field_names,
                         header_name=header_name,
                         form_url=form_url,
                         )


def waterbalance_area_edit_sub_in_single(request,
                                         area_slug,
                                         scenario_slug,
                                         pump_id,
                                         template=None):
    instance = get_object_or_404(PumpingStation, pk=int(pump_id))
    fixed_field_names = []
    form_class = PumpingStationEditForm
    form_url = reverse(
        'waterbalance_area_edit_sub_in_single',
        kwargs={'area_slug': area_slug,
                'scenario_slug': scenario_slug,
                'pump_id': pump_id})
    previous_url = reverse(
        'waterbalance_area_edit_sub_in',
        kwargs={'area_slug': area_slug, 'scenario_slug': scenario_slug})
    return _sub_edit(request,
                     area_slug=area_slug,
                     scenario_slug=scenario_slug,
                     instance=instance,
                     template=template,
                     fixed_field_names=fixed_field_names,
                     form_class=form_class,
                     form_url=form_url,
                     previous_url=previous_url,
                     )


def waterbalance_area_edit_sub_labels(request,
                                      area_slug,
                                      scenario_slug,
                                      template=None):
    conf = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    instance = conf.open_water
    fixed_field_names = []
    return _sub_edit(request,
                     area_slug=area_slug,
                     scenario_slug=scenario_slug,
                     instance=instance,
                     template=template,
                     fixed_field_names=fixed_field_names,
                     )


def waterbalance_area_edit_sub7(request,
                                area_slug,
                                scenario_slug,
                                template=None):
    conf = get_object_or_404(
        WaterbalanceConf,
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)
    instance = conf.open_water
    fixed_field_names = []
    return _sub_edit(request,
                     area=area_slug,
                     scenario_slug=scenario_slug,
                     instance=instance,
                     template=template,
                     fixed_field_names=fixed_field_names,
                     )
