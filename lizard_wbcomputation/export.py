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



import time
import logging
import xlrd
from xlutils.copy import copy
import xlwt


from timeseries.timeseriesstub import enumerate_dict_events

logger = logging.getLogger(__name__)

######################################################


def test_export():
    pass
    #TODO

def export_excel_small(waterbalance_computer, template_fileloc, output_fileloc, start_date, end_date, bucket_export=True,):
    """ export van een configuratie naar Excel """

    t1 = time.time()
    logger.debug("%s seconds - got waterbalance computer", time.time() - t1)

    rb = xlrd.open_workbook(template_fileloc, on_demand=True)
    wb = copy(rb)

    logger.debug("%s seconds - opened excel template", time.time() - t1)

    input_ts = waterbalance_computer.get_input_timeseries(start_date, end_date)
    buckets_summary = waterbalance_computer.get_bucketflow_summary(start_date, end_date)

    start_row = 13
    row = start_row

    excel_date_fmt = 'D/M/YY'
    style = xlwt.XFStyle()
    style.num_format_str = excel_date_fmt


    bucket_export = True
    #bakjes export
    if bucket_export:

        if u'bakjes' in rb.sheet_names():
            sheet = wb.sheet_by_name(u'bakjes')
        else:
            sheet = wb.add_sheet('bakje')

        buckets = waterbalance_computer.get_buckets_timeseries(start_date, end_date)

        data_cols = {}
        i = 2

        for key, bucket in buckets.items():
            print key.name

            data_cols[(i+1, 'storage', '[mm/dag]', key.name)] = bucket.storage
            data_cols[(i+2, 'flow_off', '[mm/dag]')] = bucket.flow_off
            data_cols[(i+3, 'net_drainage', '[mm/dag]')] = bucket.net_drainage
            data_cols[(i+4, 'seepage', '[mm/dag]')] = bucket.seepage
            data_cols[(i+5, 'net_precipitation', '[mm/dag]')] = bucket.net_precipitation

            i = i + 6

        row = start_row

        sheet.write(10,0,'datum')
        for key in data_cols.keys():
            sheet.write(10,key[0],key[1])
            sheet.write(11,key[0],key[2])
            if len(key) > 3:
                sheet.write(9,key[0],key[3])

        for event_dict in enumerate_dict_events(data_cols):
            date = event_dict['date']
            sheet.write(row,0,date, style)
            for key, event in event_dict.items():
                if not key == 'date':
                    sheet.write(row,key[0],event[1])

            row = row + 1
            if date > end_date:
                break




    from lizard_wbcomputation.compute import transform_evaporation_timeseries_penman_to_makkink

    sheet = wb.get_sheet(0)
    #tests
    buckets_summary = waterbalance_computer.get_bucketflow_summary(start_date, end_date)
    vertical_openwater = waterbalance_computer.get_vertical_open_water_timeseries(start_date, end_date)
    level_control = waterbalance_computer.get_level_control_timeseries(start_date, end_date)
    fractions = waterbalance_computer.get_fraction_timeseries(start_date, end_date)
    sluice_error, sluice_error_inlet = waterbalance_computer.calc_sluice_error_timeseries(start_date, end_date)
    #chloride_concentration, delta_concentration = waterbalance_computer.get_concentration_timeseries(start_date, end_date)
    impact_minimum, impact_incremental = waterbalance_computer.get_impact_timeseries(start_date, end_date)

    logger.debug("%s seconds - got all values", time.time() - t1)

    #combine cols of table
    header = ['year', 'month', 'day']
    data_cols = {}
    data_cols[(2, 'neerslag', '[mm/dag]')] = input_ts['precipitation']
    data_cols[(3, 'verdamping', '[mm/dag]')] = input_ts['evaporation']
    data_cols[(4, 'verdamping', '[mm/dag]')] = transform_evaporation_timeseries_penman_to_makkink(input_ts['evaporation'])
    data_cols[(5, 'min peil', '[mNAP]')] = input_ts['open_water']['minimum_level']
    data_cols[(7, 'max_peil', '[mNAP]')] = input_ts['open_water']['maximum_level']
#    try:
#        data_cols[(6, 'streefpeil', '[mNAP]')] = configuration.open_water.target_level.get_timeseries()
#    except:
#        pass

    #in
    data_cols[(9, 'neerslag', '[m3/dag]')] = vertical_openwater['precipitation']
    data_cols[(10, 'verdamping', '[m3/dag]')] = vertical_openwater['seepage']
    data_cols[(11, 'verhard', '[m3/dag]')] = buckets_summary.hardened
    data_cols[(12, 'riolering', '[m3/dag]')] = buckets_summary.sewer
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
    col = 25
    for intake, timeserie in input_ts['outgoing_timeseries'].items():
        data_cols[(col, str(intake), '[m3/dag]')] = timeserie
        col = col + 1


    data_cols[(29, 'uitlaat_peilhandhaving', '[m3/dag]')] = level_control["outtake_wl_control"]

    #totaal
    data_cols[(32, 'totaal in', '[m3/dag]')] = level_control['total_incoming']
    data_cols[(33, 'totaal uit', '[m3/dag]')] = level_control['total_outgoing']
    data_cols[(35, 'berekend waterpeil', '[mNAP]')] = level_control['water_level']
    data_cols[(36, 'berekende berging', '[m3]')] = level_control['storage']

#    data_cols[(50, 'verschil chloride', '[g]')] = delta_concentration
#    data_cols[(51, 'chloride concentratie', '[mg/l]')] = chloride_concentration

    #fracties
    data_cols[(68, 'fractie initieel', '[-]')] = fractions['initial']
    data_cols[(69, 'fractie neerslag', '[-]')] = fractions['precipitation']
    data_cols[(70, 'fractie kwel', '[-]')] = fractions['seepage']
    data_cols[(71, 'fractie verhard', '[-]')] = fractions['hardened']
    data_cols[(72, 'fractie riolering', '[-]')] = fractions['sewer']
    data_cols[(73, 'fractie gedraineerd', '[-]')] = fractions['drained']
    data_cols[(74, 'fractie uitspoeling', '[-]')] = fractions['undrained']
    data_cols[(75, 'fractie uitstroom', '[-]')] = fractions['flow_off']
    colnr = 76
    for key, item in fractions['intakes'].items():
        data_cols[(colnr, 'fractie %s'%str(key), '[-]')] = item
        colnr = colnr + 1

    data_cols[(108, 'sluitfout', '[m3/dag]')] = sluice_error

#    colnr = 135
#    for key, item in impact_minimum.items():
#        data_cols[(colnr, 'min fosfaatb %s'%str(key), '[mg/m2/dag]' )] = item
#        colnr = colnr + 1
#
#    colnr = colnr + 1
#
#    for key, item in impact_incremental.items():
#        data_cols[(colnr, 'incr fosfaatb %s'%str(key), '[mg/m2/dag]')] = item
#        colnr = colnr + 1

    logger.debug("%s seconds - referenced all values", time.time() - t1)

    row = start_row

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
        if date > end_date:
            break

    #for max: Formula('MAX(A1:B1)')
    buffer = file(output_fileloc,'w')
    wb.save(buffer)
    del wb
    logger.debug("%s seconds - saved excel file to memory", time.time() - t1)

    return

