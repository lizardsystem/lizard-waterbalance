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
# Initial programmer: Pieter Swinkels
#
#******************************************************************************

from datetime import datetime
from os.path import join
import sys
import glob
import xlrd
import os
import csv
    
from django.core.management.base import BaseCommand

from lizard_waterbalance.models import WaterbalanceArea, WaterbalanceScenario, WaterbalanceConf, Parameter, WaterbalanceTimeserie, Timeseries, OpenWater, \
                                        Bucket, PumpingStation, PumpLine
from timeseries.timeseriesstub import TimeseriesStub
from django.contrib.gis.geos import GEOSGeometry


def save_timeserie_into_database(wb_timeserie, sheet, row, date_col, value_col):

    #set timeserie settings
    timeserie_stub = TimeseriesStub()
    wb_timeserie.use_fews = False
    
    try:
        for rownr in range(row,row+10000):
            try:
                date = xlrd.xldate_as_tuple(sheet.cell(rownr,date_col).value,0)
                value = float(sheet.cell(rownr,value_col).value)
                timeserie_stub.add_value(datetime(date[0],date[1],date[2]), value)
            except ValueError:
                #skip timestamp
                pass
                
    except IndexError:
       pass

    if wb_timeserie.local_timeseries:
        timeseries = wb_timeserie.local_timeseries
        timeseries.timeseries_events.all().delete()
    else:
        timeseries = Timeseries.objects.create(name = wb_timeserie.name)
        wb_timeserie.local_timeseries = timeseries

    print 'start save timeserie %s'%datetime.now()
    timeseries.save_timeserie_stub(timeserie_stub)
    print 'finish save timeserie %s'%datetime.now()
    wb_timeserie.save()

def create_save_yearly_timeserie_into_database(wb_timeserie, array_date_value, start_year=1996, end_year=2015):

    #set timeserie settings
    timeserie_stub = TimeseriesStub()
    wb_timeserie.use_fews = False
    

    for year in range(start_year, end_year):
        for month, day, value in array_date_value:
            timeserie_stub.add_value(datetime(year, month, day), value)

    if wb_timeserie.local_timeseries:
        timeseries = wb_timeserie.local_timeseries
        timeseries.timeseries_events.all().delete()
    else:
        timeseries = Timeseries.objects.create(name = wb_timeserie.name)
        wb_timeserie.local_timeseries = timeseries

    print 'start save timeserie %s'%datetime.now()
    timeseries.save_timeserie_stub(timeserie_stub)
    print 'finish save timeserie %s'%datetime.now()
    wb_timeserie.save()



def upload_settings_from_excelfile(xls_file_name, load_excel_reference_results=True):
    """load settings from the waternet excelfile format
    
    """

    print 'start import file %s'%xls_file_name
   
    start_year = 1996
    last_year = 2015
    xls = xlrd.open_workbook(xls_file_name)
    sheet = xls.sheet_by_name('uitgangspunten')
    
    wb_area_name = sheet.cell(0,0).value
    
    par_rainfall_day, new = Parameter.objects.get_or_create(name='dag neerslag', unit='mm/dag')
    par_evaporation_day, new = Parameter.objects.get_or_create(name='dag verdamping', unit='mm/dag')
    par_min_level, new = Parameter.objects.get_or_create(name='minimum waterpeil', unit='mNAP')
    par_max_level, new = Parameter.objects.get_or_create(name='minimum waterpeil', unit='mNAP')
    par_reference_waterlevel_day, new = Parameter.objects.get_or_create(name='gemeten waterpeil', unit='mNAP')
    par_seepage_infiltration, new = Parameter.objects.get_or_create(name='kwel(+) en wegzijging(-)', unit='mm/dag')
    par_seepage, new = Parameter.objects.get_or_create(name='kwel', unit='mm/dag')
    par_infiltration, new = Parameter.objects.get_or_create(name='wegzijging', unit='mm/dag')
    par_structure_discharge, new = Parameter.objects.get_or_create(name='kunstwerk_debiet', unit='m3/dag')
    par_chloride_measurement, new = Parameter.objects.get_or_create(name='gemeten chloride', unit='mg/l')
    
    try:
        area = WaterbalanceArea.objects.get(name=wb_area_name)
        scenario = WaterbalanceScenario.objects.get_or_create(name='import')
    except (WaterbalanceArea.DoesNotExist):
        print "geometry van gebied %s niet gevonden"%wb_area_name
        area, new = WaterbalanceArea.objects.get_or_create(name="default",defaults={'geom':GEOSGeometry('MULTIPOLYGON(((1 1,0 1,0 1,1 1)))')})
        
    
        #create scenario with name and link areas later manually
        scenario, new = WaterbalanceScenario.objects.get_or_create(name=wb_area_name)
        
    config, new = WaterbalanceConf.objects.get_or_create(waterbalance_scenario = scenario, waterbalance_area = area)
    
    config.description = area.name
    config.slug = config.__unicode__()
    
    #precipitation
    parameter = par_rainfall_day
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_precipitation=config).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__(), parameter.name ))
        config.precipitation = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_precipitation=config)[0]                 
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 1)
    
    #evaporation
    parameter = par_evaporation_day
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_evaporation=config).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__(), parameter.name ))
        config.evaporation = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_evaporation=config)[0]                 
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 2)
    
    WaterbalanceTimeserie.objects.filter(configuration_references=config)
    #references - todo
    #reference - waterlevel
    parameter = par_reference_waterlevel_day
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__(), parameter.name ))
        config.references.add(wb_timeserie)
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config)[0]                 
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 4)
    
    #reference - chloride
    parameter = par_chloride_measurement
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__(), parameter.name ))
        config.references.add(wb_timeserie)
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config)[0]                 
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 22)
    
    
    #results - todo
    if config.open_water:
        open_water = config.open_water
    else:
        open_water = OpenWater()
        
    
    
    ######################### OpenWater ##############################
    open_water.name = config.__unicode__()
    open_water.surface = sheet.cell(10,3).value
    open_water.bottom_height = sheet.cell(11,3).value #is average depth
    open_water.init_water_level = sheet.cell(67,3).value
    open_water.save()
    
    config.open_water = open_water
    config.save()
    
    #minimum_level
    array_with_values = [[1,1,float(sheet.cell(66,2).value)],
                         [3,15,float(sheet.cell(63,2).value)],
                         [5,1,float(sheet.cell(64,2).value)],
                         [8,15,float(sheet.cell(65,2).value)],
                         [10,1,float(sheet.cell(66,2).value)],
                        ]
    parameter = par_min_level
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_min_level=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__(), parameter.name ))
        open_water.minimum_level = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_min_level=open_water)[0]                 
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
    
    #maximum_level
    array_with_values = [[1,1,float(sheet.cell(66,4).value)],
                         [3,15,float(sheet.cell(63,4).value)],
                         [5,1,float(sheet.cell(64,4).value)],
                         [8,15,float(sheet.cell(65,4).value)],
                         [10,1,float(sheet.cell(66,4).value)],
                        ]
    parameter = par_max_level
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_max_level=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__(), parameter.name ))
        open_water.maximum_level = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_max_level=open_water)[0]                 
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
        
    #target_level, wordt niet gebruikt, weg?
    
    #seepage
    array_with_values = [[1,1,float(sheet.cell(36,1).value)]]
    parameter = par_seepage
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_seepage=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__(), parameter.name ))
        open_water.seepage = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_seepage=open_water)[0]                 
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
    
    array_with_values = [[1,1,float(sheet.cell(36,1).value)]]
    parameter = par_infiltration
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_infiltration=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__(), parameter.name ))
        open_water.infiltration = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_infiltration=open_water)[0]                 
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
    
    open_water.save()
    
    ######################### Buckets ##############################
    
    
    
    
    
    bucket_nr = 0
    for colnr in range(4,12):
        if sheet.cell(34, colnr).value > 0 and (sheet.cell(34, colnr).value < sheet.cell(34, colnr+1).value or sheet.cell(34, colnr+1).value < 0):
            bucket_nr = bucket_nr + 1
            
            if sheet.cell(34, colnr).value == sheet.cell(34, colnr-1).value:
                #dubble bucket
                print 'dubbel bucket: %s'%sheet.cell(35, colnr-1).value
                col_upper = colnr-1
                col_lower = colnr
                
                name = sheet.cell(35, col_upper).value
    
                if name.find('verhard') >= 0:
                    surface_type = Bucket.HARDENED_SURFACE
                elif name.find('gedraineerd') >= 0:
                    surface_type = Bucket.DRAINED_SURFACE
                else:
                    print 'ERROR: bucket type "%s"unknown, take drained'%name
                    surface_type = Bucket.DRAINED_SURFACE
    
            else:
                #single bucket
                print 'single bucket: %s'%sheet.cell(35, colnr).value
                col_upper = colnr
                col_lower = colnr
                
                name = sheet.cell(35, col_upper).value
    
                if name.find('stedelijk') >= 0:
                    bucket.surface_type = Bucket.STEDELIJK_SURFACE
                elif name.find('ondraineerd') >= 0:
                    bucket.surface_type = Bucket.UNDRAINED_SURFACE
                elif name.lower().find('verhard') >= 0:
                    bucket.surface_type = Bucket.HARDENED_SURFACE
                elif name.lower().find('landelijk') >= 0:
                    bucket.surface_type = Bucket.DRAINED_SURFACE                    
                else:
                    print 'ERROR: bucket type "%s" unknown, take drained'%name
                    bucket.surface_type = Bucket.DRAINED_SURFACE
    
            if Bucket.objects.filter(open_water=open_water, name=name, surface_type=surface_type).count()>0:
                bucket = Bucket.objects.filter(open_water=open_water, name=name, surface_type=surface_type)[0]
            else:
                bucket = Bucket()
    
            bucket.name = name
            bucket.surface_type = surface_type
            bucket.slug = sheet.cell(35, col_upper).value
            bucket.surface = sheet.cell(43, col_upper).value
            bucket.open_water = open_water
    
            #upper
            if bucket.surface_type == Bucket.HARDENED_SURFACE:
                bucket.crop_evaporation_factor = 1
                bucket.min_crop_evaporation_factor = 1            
            else:
                bucket.crop_evaporation_factor = 1
                bucket.min_crop_evaporation_factor = 0.75
            
            bucket.upper_porosity = sheet.cell(38, col_upper).value
            bucket.upper_drainage_fraction = sheet.cell(36, col_upper).value
            bucket.upper_indraft_fraction = sheet.cell(37, col_upper).value
            bucket.upper_max_water_level = sheet.cell(39, col_upper).value
            bucket.upper_equi_water_level = 0
            if type(sheet.cell(41, col_upper).value) == type(1) or type(sheet.cell(41, col_upper).value) == type(1.0):
                bucket.upper_min_water_level = sheet.cell(41, col_upper).value
            else:
                bucket.upper_min_water_level = None
    
            bucket.upper_init_water_level = sheet.cell(42, col_upper).value
    
            #lower
            
            bucket.porosity = sheet.cell(38, col_lower).value
            bucket.drainage_fraction = sheet.cell(36, col_lower).value
            bucket.indraft_fraction = sheet.cell(37, col_lower).value
            bucket.max_water_level = sheet.cell(39, col_lower).value
            bucket.equi_water_level = 0
    
            if type(sheet.cell(41, col_lower).value) == type(1) or type(sheet.cell(41, col_lower).value) == type(1.0):
                bucket.min_water_level = sheet.cell(41, col_lower).value
            else:
                bucket.min_water_level = None
                
            bucket.init_water_level = sheet.cell(42, col_lower).value
            bucket.save()
            #bucket.seepage
    
    
            array_with_values = [[1,1,float(sheet.cell(37+bucket_nr,1).value)]]
            parameter = par_seepage_infiltration
            if WaterbalanceTimeserie.objects.filter(parameter=parameter, bucket_seepage=bucket).count() == 0:
                wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(bucket.__unicode__(), parameter.name ))
                bucket.seepage = wb_timeserie
            else:
                wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, bucket_seepage=bucket)[0]                 
            create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
    
            bucket.save()
    
            #results
    
        
    
        
    ################# PUMPINGSTATIONS ################
        
    
    
    #inlaat peilhandhaving
    if PumpingStation.objects.filter(open_water=open_water, name='inlaat peilhandhaving').count() > 0:
        pumping_station = PumpingStation.objects.filter(open_water=open_water, name='inlaat peilhandhaving')[0]
    else:
        pumping_station = PumpingStation()
        pumping_station.open_water = open_water
        pumping_station.name = 'inlaat peilhandhaving'
    
    pumping_station.into = True
    pumping_station.percentage = 100
    pumping_station.computed_level_control = True
    if type(sheet.cell(69,1)).value==type(1) or type(sheet.cell(69,1)).value==type(1.0):
        pumping_station.max_discharge = sheet.cell(69,1).value
    pumping_station.save()
    for colnr in range(9,9):
        if (not sheet.cell(72,colnr).value == None) and len(sheet.cell(72,colnr).value)>0:
            name = "%s_%i"%(sheet.cell(72,colnr), colnr-3)
            if PumpLine.objects.filter(pumping_station=pumping_station, name=name):
                pump_line = PumpLine.objects.filter(pumping_station=pumping_station, name=name)[0]
            else:
                pump_line = PumpLine()
                pump_line.pumping_station = pumping_station
                pump_line.name = name
                pump_line.save()
    
            
            parameter = par_structure_discharge
            if WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line).count() == 0:
                wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__(), parameter.name ))
                pump_line.timeserie = wb_timeserie  
            else:
                wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line)[0]                 
            save_timeserie_into_database(wb_timeserie, sheet, 76, 0, colnr)
            
            pump_line.save()
    
    inlaat_peilhandhaving = pumping_station   
        
    #uitlaat peilhandhaving
    if PumpingStation.objects.filter(open_water=open_water, name='uitlaat peilhandhaving').count() > 0:
        pumping_station = PumpingStation.objects.filter(open_water=open_water, name='uitlaat peilhandhaving')[0]
    else:
        pumping_station = PumpingStation()
        pumping_station.open_water = open_water
        pumping_station.name = 'uitlaat peilhandhaving'
    pumping_station.into = False
    pumping_station.percentage = 100
    pumping_station.computed_level_control = True
    if type(sheet.cell(70,1).value)==type(1) or type(sheet.cell(70,1).value)==type(1.0):
        pumping_station.max_discharge = sheet.cell(70,1).value
    pumping_station.save()
    for colnr in range(4, 8):
        if (not sheet.cell(72,colnr).value == None) and len(sheet.cell(72,colnr).value)>0:
            name = "%s_%i"%(sheet.cell(72,colnr).value, colnr-3)
            if PumpLine.objects.filter(pumping_station=pumping_station, name=name):
                pump_line = PumpLine.objects.filter(pumping_station=pumping_station, name=name)[0]
            else:
                pump_line = PumpLine()
                pump_line.pumping_station = pumping_station
                pump_line.name = name
                pump_line.save()
    
            
            parameter = par_structure_discharge
            if WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line).count() == 0:
                wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__(), parameter.name ))
                pump_line.timeserie = wb_timeserie  
            else:
                wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line)[0]                 
            save_timeserie_into_database(wb_timeserie, sheet, 76, 0, colnr)
            
            pump_line.save()
    
    uitlaat_peilhandhaving = pumping_station   
       
    #inlaten opgedrukt
    
    for row in range(23,31):
        if sheet.cell(row,1).value == 0 and sheet.cell(row,2).value == 0:
            pass
        elif sheet.cell(row,1).value == 'rekenhart':
            pass
        else:
            name = sheet.cell(row,0).value
            if PumpingStation.objects.filter(open_water=open_water, name=name).count() > 0:
                pumping_station = PumpingStation.objects.filter(open_water=open_water, name=name)[0]
            else:
                pumping_station = PumpingStation()
                pumping_station.open_water = open_water
                pumping_station.name = name
            if row > 27:
                pumping_station.into = False
            else:
                pumping_station.into = True
            pumping_station.percentage = 100
            pumping_station.computed_level_control = False
            pumping_station.max_discharge = None
            pumping_station.save()
            
            if PumpLine.objects.filter(pumping_station=pumping_station, name=name):
                pump_line = PumpLine.objects.filter(pumping_station=pumping_station, name=name)[0]
            else:
                pump_line = PumpLine()
                pump_line.pumping_station = pumping_station
                pump_line.name = pumping_station.name
                pump_line.save()
    
            #discharge
            array_with_values = [[1,1,float(sheet.cell(row,1).value)],
                                 [4,1,float(sheet.cell(row,2).value)],
                                 [10,1,float(sheet.cell(row,1).value)],
                                ]
            parameter = par_structure_discharge
            if WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line).count() == 0:
                wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__(), parameter.name ))
                pump_line.timeserie = wb_timeserie
            else:
                wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line)[0]                 
            create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
            pump_line.save()
                

    par_structure_discharge_excel, new = Parameter.objects.get_or_create(name='debiet excel', unit='m3/dag')
    
    if load_excel_reference_results:
        sheet_resultaten = xls.sheet_by_name('REKENHART')
                
        parameter = par_structure_discharge_excel
        if WaterbalanceTimeserie.objects.filter(parameter=parameter, pumping_station_result=uitlaat_peilhandhaving).count() == 0:
            wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(uitlaat_peilhandhaving.__unicode__(), parameter.name ))
            uitlaat_peilhandhaving.results.add(wb_timeserie)
        else:
            wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pumping_station_result=uitlaat_peilhandhaving)[0]                 
        save_timeserie_into_database(wb_timeserie, sheet_resultaten, 13, 0, 29)
        
        parameter = par_structure_discharge_excel
        if WaterbalanceTimeserie.objects.filter(parameter=parameter, pumping_station_result=inlaat_peilhandhaving).count() == 0:
            wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(inlaat_peilhandhaving.__unicode__(), parameter.name ))
            inlaat_peilhandhaving.results.add(wb_timeserie)
        else:
            wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pumping_station_result=inlaat_peilhandhaving)[0]                 
        save_timeserie_into_database(wb_timeserie, sheet_resultaten, 13, 0, 20)


class Command(BaseCommand):
    args = "<directory_with_excelfiles>"
    help = "Load all waternet waterbalance excelfiles from a directory (only xls)."

    def handle(self, *args, **options):
        directory = str(args[0])
        load_excel_reference_results = True

        input_path = join(directory, "*.xls")

        for xls_file_name in glob.glob(input_path):
            upload_settings_from_excelfile(xls_file_name, load_excel_reference_results) 




