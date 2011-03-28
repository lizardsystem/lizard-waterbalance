#!/usr/bin/python
# -*- coding: utf-8 -*-
#******************************************************************************
#
# This file is part of the lizard_waterbalance Django app.
#
# The lizard_waterbalance app is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# the lizard_waterbalance app.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010 Nelen & Schuurmans
#
#******************************************************************************
#
# Initial programmer: Bastiaan Roos
# Initial date:       2011-03-20
#
#******************************************************************************



from datetime import datetime
import time
import logging
import xlrd
from xlutils.copy import copy
import xlwt
from cStringIO import StringIO
import pkg_resources

from django.http import HttpResponse

from lizard_waterbalance.models import WaterbalanceConf

from timeseries.timeseriesstub import enumerate_dict_events

logger = logging.getLogger(__name__)

#configuration = WaterbalanceConf.objects.all()[1]
#waterbalance_computer = WaterbalanceComputer2(configuration)
#waterbalance_computer.get_buckets_timeseries(start_year, end_year)

######################################################


def test_export():
    start_date = datetime(1996,01,01)
    end_date = datetime(2009,01,01)

    configuration_slug = 'aetsveldsche_polder_oost_-_test'
    export_to_excel(configuration_slug, start_date, end_date)

def export_excel_small(request, area_slug, scenario_slug):
    """ export van een configuratie naar Excel """

    t1 = time.time()

    bucket_export = False

    configuration = WaterbalanceConf.objects.get(
        waterbalance_area__slug=area_slug,
        waterbalance_scenario__slug=scenario_slug)

    waterbalance_computer = configuration.get_waterbalance_computer()

    logger.debug("%s seconds - got waterbalance computer", time.time() - t1)

    start_date = configuration.calculation_start_date
    end_date = datetime.now()
    end_date = datetime(end_date.year, end_date.month, end_date.day)

    excel_template = pkg_resources.resource_filename("lizard_waterbalance",
                                                     "/templates/lizard_waterbalance/excel_export_template.xls")

    rb = xlrd.open_workbook(excel_template, on_demand=True)
    wb = copy(rb)

    logger.debug("%s seconds - opened excel template", time.time() - t1)

    input_ts = waterbalance_computer.get_input_timeseries(start_date, end_date)
    buckets_summary = waterbalance_computer.get_bucketflow_summary(start_date, end_date)

    #bakjes export
    if bucket_export:

        if u'bakjes' in rb.sheet_names():
            sheet = wb.sheet_by_name(u'bakjes')
        else:
            sheet = wb.add_sheet('bakje')

        buckets = waterbalance_computer.get_buckets_timeseries(start_date, end_date)

        #TO DO: afmaken


    sheet = wb.get_sheet(0)
    #tests
    buckets_summary = waterbalance_computer.get_bucketflow_summary(start_date, end_date)
    vertical_openwater = waterbalance_computer.get_vertical_open_water_timeseries(start_date, end_date)
    level_control = waterbalance_computer.get_level_control_timeseries(start_date, end_date)
    fractions = waterbalance_computer.get_fraction_timeseries(start_date, end_date)
    sluice_error = waterbalance_computer.calc_sluice_error_timeseries(start_date, end_date)
    chloride_concentration, delta_concentration = waterbalance_computer.get_concentration_timeseries(start_date, end_date)
    impact_minimum, impact_incremental = waterbalance_computer.get_impact_timeseries(configuration.open_water, start_date, end_date)

    logger.debug("%s seconds - got all values", time.time() - t1)

    waterbalance_computer.cache_if_updated()
    logger.debug("%s seconds - saved to cache", time.time() - t1)



    #combine cols of table
    header = ['year', 'month', 'day']
    data_cols = {}
    data_cols[(2, 'neerslag', '[mm/dag]')] = input_ts['precipitation']
    data_cols[(3, 'neerslag', '[mm/dag]')] = input_ts['evaporation']
    data_cols[(5, 'min peil', '[mNAP]')] = configuration.open_water.minimum_level.get_timeseries()
    data_cols[(7, 'neerslag', '[mNAP]')] = configuration.open_water.maximum_level.get_timeseries()
    try:
        data_cols[(6, 'streefpeil', '[mNAP]')] = configuration.open_water.target_level.get_timeseries()
    except:
        pass

    #in
    data_cols[(9, 'neerslag', '[m3/dag]')] = vertical_openwater['precipitation']
    data_cols[(10, 'verdamping', '[m3/dag]')] = vertical_openwater['seepage']
    data_cols[(11, 'verhard', '[m3/dag]')] = buckets_summary.hardened
    data_cols[(13, 'gedraineerd', '[m3/dag]')] = buckets_summary.drained
    data_cols[(14, 'uitspoelig', '[m3/dag]')] = buckets_summary.undrained
    data_cols[(15, 'afstroming', '[m3/dag]')] = buckets_summary.flow_off
    col = 16
    for intake, timeserie in input_ts['incoming_timeseries'].items():
        data_cols[(col, str(intake), '[m3/dag]')] = timeserie
        col = col + 1

    data_cols[(20, 'inlaat peilhandhaving', '[m3/dag]')] = level_control["intake_wl_control"]

    #uit
    data_cols[(22, 'verdamping', '[m3/dag]')] = vertical_openwater['evaporation']
    data_cols[(23, 'wegzijiging', '[m3/dag]')] = vertical_openwater['infiltration']
    data_cols[(24, 'intrek', '[m3/dag]')] = buckets_summary.indraft
    data_cols[(29, 'uitlaat', '[m3/dag]')] = level_control["outtake_wl_control"]

    #totaal
    data_cols[(32, 'totaal in', '[m3/dag]')] = level_control['total_incoming']
    data_cols[(33, 'totaal uit', '[m3/dag]')] = level_control['total_outgoing']
    data_cols[(35, 'berekend waterpeil', '[mNAP]')] = level_control['water_level']
    data_cols[(36, 'berekende berging', '[m3]')] = level_control['storage']
    
    data_cols[(50, 'verschil chloride', '[g]')] = delta_concentration
    data_cols[(51, 'chloride concentratie', '[mg/l]')] = chloride_concentration

    #fracties
    data_cols[(68, 'fractie initieel', '[-]')] = fractions['initial']
    data_cols[(69, 'fractie neerslag', '[-]')] = fractions['precipitation']
    data_cols[(70, 'fractie kwel', '[-]')] = fractions['seepage']
    data_cols[(71, 'fractie verhard', '[-]')] = fractions['hardened']
    data_cols[(73, 'fractie gedraineerd', '[-]')] = fractions['drained']
    data_cols[(74, 'fractie uitspoeling', '[-]')] = fractions['undrained']
    data_cols[(75, 'fractie uitstroom', '[-]')] = fractions['flow_off']
    colnr = 76
    for key, item in fractions['intakes'].items():
        data_cols[(colnr, 'fractie %s'%str(key), '[-]')] = item
        colnr = colnr + 1

    data_cols[(108, 'sluitfout', '[m3/dag]')] = sluice_error[0]
    data_cols[(111, 'som gemeten pompdebieten', '[m3/dag]')] = sluice_error[1]

    colnr = 135
    for key, item in impact_minimum.items():
        data_cols[(colnr, 'min fosfaatb %s'%str(key), '[mg/m2/dag]' )] = item
        colnr = colnr + 1

    colnr = colnr + 1

    for key, item in impact_incremental.items():
        data_cols[(colnr, 'incr fosfaatb %s'%str(key), '[mg/m2/dag]')] = item
        colnr = colnr + 1

    start_row = 13
    row = start_row


    excel_date_fmt = 'D/M/YY'
    style = xlwt.XFStyle()
    style.num_format_str = excel_date_fmt

    logger.debug("%s seconds - referenced all values", time.time() - t1)

    sheet.write(10,0,'datum')
    for key in data_cols.keys():
        sheet.write(10,key[0],key[1])
        sheet.write(11,key[0],key[2])

    for event_dict in enumerate_dict_events(data_cols):
        date = event_dict['date']
        sheet.write(row,0,date, style)
        for key, event in event_dict.items():
            if not key == 'date':
                sheet.write(row,key[0],event[1])

        row = row + 1
    
    #for max: Formula('MAX(A1:B1)')
    buffer = StringIO()
    wb.save(buffer)
    del wb
    logger.debug("%s seconds - saved excel file to memory", time.time() - t1)

    buffer.seek(0)
    response = HttpResponse(buffer.read(), mimetype='xls')
    today = datetime.now()
    response['Content-Disposition'] = \
                'attachment; filename=wb_export_%s_%s_%i-%i-%i.xls'% \
                    (configuration.waterbalance_area.slug[:25],
                     configuration.waterbalance_scenario.slug[:20],
                     today.day, today.month, today.year)

    return  response

