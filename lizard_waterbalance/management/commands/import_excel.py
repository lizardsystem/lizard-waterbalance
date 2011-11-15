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
import glob
import xlrd


from django.core.management.base import BaseCommand

from lizard_waterbalance.models import Bucket
from lizard_waterbalance.models import Concentration
from lizard_waterbalance.models import Label
from lizard_waterbalance.models import OpenWater
from lizard_waterbalance.models import Parameter
from lizard_waterbalance.models import PumpLine
from lizard_waterbalance.models import PumpingStation
from lizard_waterbalance.models import Timeseries
from lizard_waterbalance.models import WaterbalanceArea
from lizard_waterbalance.models import WaterbalanceConf
from lizard_waterbalance.models import WaterbalanceScenario
from lizard_waterbalance.models import WaterbalanceTimeserie

from lizard_wbcomputation.bucket_types import BucketTypes

from timeseries.timeseriesstub import TimeseriesStub

NAME_INTAKE_LEVEL_CONTROL = "inlaat peilhandhaving"
COORDS_MAX_DISCHARGE_INTAKE_LEVEL_CONTROL = [69, 1]
COORDS_NAME_PUMPLINE_INTAKE_LEVEL_CONTROL = [72, 8]

def save_timeserie_into_database(wb_timeserie, sheet, row, date_col, value_col, stick_to_last_value=False):

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
        timeseries.stick_to_last_value=stick_to_last_value
        timeseries.timeseries_events.all().delete()
    else:
        timeseries = Timeseries.objects.create(name = wb_timeserie.name,  stick_to_last_value=stick_to_last_value)
        wb_timeserie.local_timeseries = timeseries

    print 'start save timeserie %s'%datetime.now()
    timeseries.save_timeserie_stub(timeserie_stub)
    print 'finish save timeserie %s'%datetime.now()
    wb_timeserie.save()

def create_save_yearly_timeserie_into_database(wb_timeserie, array_date_value, start_year=1996, end_year=2015, stick_to_last_value=True):

    #set timeserie settings
    timeserie_stub = TimeseriesStub()
    wb_timeserie.use_fews = False


    for year in range(start_year, end_year):
        for month, day, value in array_date_value:
            timeserie_stub.add_value(datetime(year, month, day), value)

    if wb_timeserie.local_timeseries:
        timeseries = wb_timeserie.local_timeseries
        timeseries.stick_to_last_value=True
        timeseries.timeseries_events.all().delete()
    else:
        timeseries = Timeseries.objects.create(name = wb_timeserie.name, stick_to_last_value=True)
        wb_timeserie.local_timeseries = timeseries

    print 'start save timeserie %s'%datetime.now()
    timeseries.save_timeserie_stub(timeserie_stub)
    print 'finish save timeserie %s'%datetime.now()
    wb_timeserie.save()


def retrieve_pumping_station_for_level_control(sheet, open_water, label):
    """Return the single PumpingStation for level control.

    This method finds the PumpingStation named NAME_INTAKE_LEVEL_CONTROL or
    creates one with that name if it does not exist.

    Note that whether such a PumpingStation exists or has to be created, this
    method (re)sets it to be an intake for level control.

    Parameters:
      * open_water *
        OpenWater to which the PumpingStation to retrieve belongs
      * labels *
        dictionary of PumpingStation name to Label

    """
    name = NAME_INTAKE_LEVEL_CONTROL
    pumping_stations = PumpingStation.objects.filter(open_water=open_water, \
        name=name)
    if pumping_stations.count() > 0:
        pumping_station = pumping_stations[0]
    else:
        pumping_station = PumpingStation()
        pumping_station.open_water = open_water
        pumping_station.name = name

    pumping_station.into = True
    pumping_station.percentage = 100
    pumping_station.computed_level_control = True
    pumping_station.label = label

    cell = sheet.cell(*COORDS_MAX_DISCHARGE_INTAKE_LEVEL_CONTROL)
    if type(cell).value == type(1) or type(cell).value == type(1.0):
        pumping_station.max_discharge = cell.value

    pumping_station.save()

    return pumping_station

def retrieve_intake_for_level_control(open_water, labels, sheet, pars):
    """Return the single intake for level control.

    This method finds the PumpingStation named NAME_INTAKE_LEVEL_CONTROL or
    creates one with that name if it does not exist. It also finds or creates
    each PumpLine for this PumpingStation and connects that PumpLine to its
    time series.

    Parameters:
      * open_water *
        OpenWater to which the PumpingStation to retrieve belongs
      * labels *
        dictionary of PumpingStation name to Label
      * sheet *
        xlrd Sheet that contains all data
      * pars *
        dictionary of PumpingStation name to Parameter

    """
    label = labels[NAME_INTAKE_LEVEL_CONTROL]
    pumping_station = retrieve_pumping_station_for_level_control(sheet,
        open_water, label)

    row, column = tuple(COORDS_NAME_PUMPLINE_INTAKE_LEVEL_CONTROL)
    cell = sheet.cell(row, column)
    if (not cell.value is None) and len(cell.value) > 0:
        name = "%s" % cell.value

        print 'pomplijn voor %s op %d, %d met naam %s' % \
             (pumping_station.__unicode__(), row, column, name)
        pump_lines = PumpLine.objects.filter(pumping_station=pumping_station, \
            name=name)
        if pump_lines.count() > 0:
            pump_line = pump_lines[0]
        else:
            pump_line = PumpLine()
            pump_line.pumping_station = pumping_station
            pump_line.name = name

        parameter = pars['structure_discharge']
        timeseries_queryset = WaterbalanceTimeserie.objects.filter(parameter=parameter,\
            pump_line_timeserie=pump_line)
        if timeseries_queryset.count() > 0:
            timeseries = timeseries_queryset[0]
        else:
            timeseries = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__()[:30], parameter.name[:15] ))
            pump_line.timeserie = timeseries

        save_timeserie_into_database(timeseries, sheet, 76, 0, column)

        pump_line.save()

def upload_settings_from_excelfile(xls_file_name, load_excel_reference_results=False):
    """load settings from the waternet excelfile format

    """

    print 'start import file %s'%xls_file_name

    xls = xlrd.open_workbook(xls_file_name)
    sheet = xls.sheet_by_name('uitgangspunten')

    wb_area_name = sheet.cell(0,0).value


    pars = {}

    pars['rainfall_day'], new = Parameter.objects.get_or_create(name='dag neerslag', unit='mm/dag', parameter = Parameter.PARAMETER_PRECIPITATION, sourcetype = Parameter.TYPE_MEASURED)
    pars['evaporation_day'], new = Parameter.objects.get_or_create(name='dag verdamping', unit='mm/dag', parameter = Parameter.PARAMETER_EVAPORATION, sourcetype = Parameter.TYPE_MEASURED)
    pars['min_level'], new = Parameter.objects.get_or_create(name='minimum waterpeil', unit='mNAP', parameter = Parameter.PARAMETER_WATERLEVEL, sourcetype = Parameter.TYPE_USERINPUT)
    pars['max_level'], new = Parameter.objects.get_or_create(name='maximum waterpeil', unit='mNAP', parameter = Parameter.PARAMETER_WATERLEVEL, sourcetype = Parameter.TYPE_USERINPUT)
    pars['reference_waterlevel_day'], new = Parameter.objects.get_or_create(name='gemeten waterpeil', unit='mNAP', parameter = Parameter.PARAMETER_WATERLEVEL, sourcetype = Parameter.TYPE_MEASURED)
    pars['seepage_infiltration'], new = Parameter.objects.get_or_create(name='kwel(+) en wegzijging(-)', unit='mm/dag', parameter = Parameter.PARAMETER_SEEPAGE_INFILTRATION, sourcetype = Parameter.TYPE_USERINPUT)
    pars['seepage'], new = Parameter.objects.get_or_create(name='kwel', unit='mm/dag', parameter = Parameter.PARAMETER_SEEPAGE_INFILTRATION, sourcetype = Parameter.TYPE_USERINPUT)
    pars['infiltration'], new = Parameter.objects.get_or_create(name='wegzijging', unit='mm/dag', parameter = Parameter.PARAMETER_SEEPAGE_INFILTRATION, sourcetype = Parameter.TYPE_USERINPUT)
    pars['structure_discharge'], new = Parameter.objects.get_or_create(name='kunstwerk_debiet', unit='m3/dag', parameter = Parameter.PARAMETER_DISCHARGE, sourcetype = Parameter.TYPE_MEASURED)
    pars['chloride_measurement'], new = Parameter.objects.get_or_create(name='gemeten chloride', unit='mg/l', parameter = Parameter.PARAMETER_CHLORIDE, sourcetype = Parameter.TYPE_MEASURED)
    pars['sewer_day'], new = Parameter.objects.get_or_create(name='referentie gemengde riolering', unit='m3/dag/ha', sourcetype = Parameter.TYPE_USERINPUT)

    try:
        area = WaterbalanceArea.objects.get(name=wb_area_name)
        scenario, new = WaterbalanceScenario.objects.get_or_create(name='import')
    except (WaterbalanceArea.DoesNotExist):
        print "geometry van gebied %s niet gevonden"%wb_area_name
        area, new = WaterbalanceArea.objects.get_or_create(name="%s n.g."%wb_area_name)
        #create scenario with name and link areas later manually
        scenario, new = WaterbalanceScenario.objects.get_or_create(name='import')


    config, config_new = WaterbalanceConf.objects.get_or_create(waterbalance_scenario=scenario, waterbalance_area=area,
                                                             defaults = {'calculation_start_date':datetime(1996,1,1),
                                                                         'description':"%s - %s"%(str(area.name), str(scenario.name))})


    labels = {}
    labels[(0,'neerslag')], new = Label.objects.get_or_create(program_name='precipitation') #name='neerslag', flow_type=Label.TYPE_IN, defaucolor='#0000ff', color_increment='#ff0000')
    labels[(1,'kwel')], new = Label.objects.get_or_create(program_name='seepage') #name='kwel', flow_type=Label.TYPE_IN, color='#ffbb00', color_increment='#ff0000')
    labels[(2,'verhard')], new = Label.objects.get_or_create(program_name='hardened') #name='verhard', flow_type=Label.TYPE_IN, color='#bbbbbb', color_increment='#ff0000')
    labels[(3,'riolering')], new = Label.objects.get_or_create(program_name='sewer') #name='riolering', flow_type=Label.TYPE_IN, color='#006600', color_increment='#ff0000')
    labels[(4,'gedraineerd')], new = Label.objects.get_or_create(program_name='drained') #name='gedraineerd', flow_type=Label.TYPE_IN, color='#ff9900', color_increment='#ff0000')
    labels[(5,'uitspoeling')], new = Label.objects.get_or_create(program_name='undrained') #name='uitspoeling', flow_type=Label.TYPE_IN, color='#00ff00', color_increment='#ff0000')
    labels[(6,'afstroming')], new = Label.objects.get_or_create(program_name='flow_off') #name='afstroming', flow_type=Label.TYPE_IN, color='#008800', color_increment='#ff0000')

    labels[(7,'inlaat1')], new = Label.objects.get_or_create(program_name='inlet1')#name='inlaat 1', flow_type=Label.TYPE_IN, color='#ff00ff', color_increment='#ff0000')
    labels[(8,'inlaat2')], new = Label.objects.get_or_create(program_name='inlet2')#name='inlaat 2', flow_type=Label.TYPE_IN, color='#cc00cc', color_increment='#ff0000')
    labels[(9,'inlaat3')], new = Label.objects.get_or_create(program_name='inlet3')#name='inlaat 3',, flow_type=Label.TYPE_IN, color='#aa00aa', color_increment='#ff0000')
    labels[(10,'inlaat4')], new = Label.objects.get_or_create(program_name='inlet4')#name='inlaat 4',, flow_type=Label.TYPE_IN, color='#880088', color_increment='#ff0000')
    labels[(11,'inlaat peilhandhaving')], new = Label.objects.get_or_create(program_name='intake_wl_control')#name='inlaat peilhandhaving',, flow_type=Label.TYPE_IN, color='#440044', color_increment='#ff0000')

    labels[(-1,'initieel')], new = Label.objects.get_or_create(program_name='initial') #name='afstroming', flow_type=Label.TYPE_IN, color='#008800', color_increment='#ff0000')

    labels[(-1,'uitlaat1')], new = Label.objects.get_or_create(program_name='outtake1')#name='uitlaat 1', flow_type=Label.TYPE_OUT, color='#663399', color_increment='#ff0000')
    labels[(-1,'uitlaat2')], new = Label.objects.get_or_create(program_name='outtake2')#name='uitlaat 2', flow_type=Label.TYPE_OUT, color='#443399', color_increment='#ff0000')
    labels[(-1,'uitlaat3')], new = Label.objects.get_or_create(program_name='outtake3')#name='uitlaat 3', flow_type=Label.TYPE_OUT, color='#666699', color_increment='#ff0000')
    labels[(-1,'uitlaat4')], new = Label.objects.get_or_create(program_name='outtake4')#name='uitlaat 4', flow_type=Label.TYPE_OUT, color='#554499', color_increment='#ff0000')
    labels[(-1,'uitlaat5')], new = Label.objects.get_or_create(program_name='outtake5')#name='uitlaat 5', flow_type=Label.TYPE_OUT, color='#6633bb', color_increment='#ff0000')
    labels[(-1,'uitlaat6')], new = Label.objects.get_or_create(program_name='outtake6')#name='uitlaat 6', flow_type=Label.TYPE_OUT, color='#662288', color_increment='#ff0000')
    labels[(-1,'uitlaat peilhandhaving')], new = Label.objects.get_or_create(program_name='outtake_wl_control')#name='uitlaat peilhandhaving',  flow_type=Label.TYPE_OUT, color='#7744aa', color_increment='#ff0000')


    #lab, new = Label.objects.get_or_create(name='intrek', program_name='indraft')#, flow_type=Label.TYPE_OUT, color='#ff9911', color_increment='#ff0000')
    #lab, new = Label.objects.get_or_create(name='wegzijging', program_name='infiltration')#, flow_type=Label.TYPE_OUT, color='#444444', color_increment='#ff0000')
    #lab, new = Label.objects.get_or_create(name='verdamping', program_name='evaporation')#, flow_type=Label.TYPE_OUT, color='#0000ff', color_increment='#ff0000')
    #lab, new = Label.objects.get_or_create(name='sluitfout', program_name='sluice_error')#, flow_type=Label.TYPE_ERROR, color='#000000', color_increment='#000000')
    #lab, new = Label.objects.get_or_create(name='gemeten waterpeil', program_name='meas_waterlevel')# flow_type=Label.TYPE_OTHER, color='#0000ff', color_increment='#000000')
    #lab, new = Label.objects.get_or_create(program_name='calc_waterlevel')#name='berekend waterpeil', , flow_type=Label.TYPE_ERROR, color='#ff00ff', color_increment='#000000')
    #lab, new = Label.objects.get_or_create(program_name='initial')#name='initieel', , flow_type=Label.TYPE_ERROR, color='#222222', color_increment='#000000')
    #initieel nog invullen

    def get_float_or_default(sheet, rownr, colnr, default_value = None):
        if type(sheet.cell(rownr, colnr).value).__name__ in ['int','float']:
            return float(sheet.cell(rownr, colnr).value)
        else:
            return default_value



    for key, label in labels.items():
        rownr = key[0] + 16
        if key[0]>=0 and (type(sheet.cell(key[0]+16, 1).value).__name__ in ['str', 'unicode'] or get_float_or_default(sheet, key[0]+16, 1) is not None):
            concentration, new = Concentration.objects.get_or_create(label=label, configuration=config)

            concentration.stof_lower_concentration = get_float_or_default(sheet, rownr, 3, 0)
            concentration.stof_increment = get_float_or_default(sheet, rownr, 4, 0)

            concentration.cl_concentration = get_float_or_default(sheet, rownr, 5, 0)

            concentration.p_lower_concentration = get_float_or_default(sheet, rownr, 7, 0)
            concentration.p_incremental = get_float_or_default(sheet, rownr, 8, 0)

            concentration.n_lower_concentration = get_float_or_default(sheet, rownr, 9)
            concentration.n_incremental = get_float_or_default(sheet, rownr, 10)

            concentration.so4_lower_concentration = get_float_or_default(sheet, rownr, 11)
            concentration.so4_incremental = get_float_or_default(sheet, rownr, 12)

            concentration.save()

    labels = dict([(key[1],label) for key, label in labels.items()])


    concentration, new = Concentration.objects.get_or_create(label=labels['initieel'], configuration=config)
    concentration.stof_lower_concentration = 0
    concentration.stof_increment = 0
    concentration.cl_concentration = get_float_or_default(sheet, 32, 3, 0)
    concentration.p_lower_concentration = 0
    concentration.p_incremental = 0
    concentration.save()





    if config_new:
        WaterbalanceTimeserie.objects.filter(configuration_references=config)
        #reference - waterlevel
        parameter = pars['reference_waterlevel_day']
        if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config).count() == 0:
            wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__()[:30], parameter.name[:15] ))
            config.references.add(wb_timeserie)
        else:
            wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config)[0]
        save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 3, stick_to_last_value=True)

        #reference - chloride
        parameter = pars['chloride_measurement']
        if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config).count() == 0:
            wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__()[:30], parameter.name[:15]))
            config.references.add(wb_timeserie)
        else:
            wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config)[0]
        save_timeserie_into_database(wb_timeserie, sheet, 76, 22, 23)

        #reference - chloride
        parameter = pars['chloride_measurement']
        if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config).count() == 0:
            wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__()[:30], parameter.name[:15] ))
            config.references.add(wb_timeserie)
        else:
            wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_references=config)[0]
        save_timeserie_into_database(wb_timeserie, sheet, 76, 24, 25)

    #results - todo
    if config.open_water:
        open_water = config.open_water
        new = False
    else:
        open_water = OpenWater()
        new =True

    ######################### OpenWater ##############################

    open_water.name = config.__unicode__()
    open_water.surface = sheet.cell(10,3).value
    open_water.bottom_height = sheet.cell(11,3).value #is average depth
    open_water.init_water_level = sheet.cell(67,3).value

    #precipitation
    parameter = pars['rainfall_day']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_precipitation=config).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__()[:30], parameter.name[:15] ))
        open_water.precipitation = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_precipitation=config)[0]
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 1)

    #evaporation
    parameter = pars['evaporation_day']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_evaporation=config).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__()[:30], parameter.name[:15] ))
        open_water.evaporation = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, configuration_evaporation=config)[0]
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 2)

    #sewer
    parameter = pars['sewer_day']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_sewer=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(config.__unicode__()[:30], parameter.name[:15] ))
        open_water.sewer = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_sewer=open_water)[0]
    save_timeserie_into_database(wb_timeserie, sheet, 76, 0, 9)




    #minimum_level
    array_with_values = [[1,1,float(sheet.cell(66,2).value)],
                         [3,15,float(sheet.cell(63,2).value)],
                         [5,1,float(sheet.cell(64,2).value)],
                         [8,15,float(sheet.cell(65,2).value)],
                         [10,1,float(sheet.cell(66,2).value)],
                        ]
    parameter = pars['min_level']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_min_level=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__()[:30], parameter.name[:15] ))
        open_water.minimum_level = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_min_level=open_water)[0]
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values, stick_to_last_value=True)

    #maximum_level
    array_with_values = [[1,1,float(sheet.cell(66,4).value)],
                         [3,15,float(sheet.cell(63,4).value)],
                         [5,1,float(sheet.cell(64,4).value)],
                         [8,15,float(sheet.cell(65,4).value)],
                         [10,1,float(sheet.cell(66,4).value)],
                        ]
    parameter = pars['max_level']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_max_level=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__()[:30], parameter.name[:15] ))
        open_water.maximum_level = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_max_level=open_water)[0]
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)

    #target_level, wordt niet gebruikt, weg?

    #seepage
    array_with_values = [[1,1,float(sheet.cell(36,1).value)]]
    parameter = pars['seepage']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_seepage=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__()[:30], parameter.name[:15] ))
        open_water.seepage = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_seepage=open_water)[0]
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)

    array_with_values = [[1,1,float(sheet.cell(36,1).value)]]
    parameter = pars['infiltration']
    if WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_infiltration=open_water).count() == 0:
        wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(open_water.__unicode__()[:30], parameter.name[:15] ))
        open_water.infiltration = wb_timeserie
    else:
        wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, open_water_infiltration=open_water)[0]
    create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)

    open_water.save()

    config.open_water = open_water
    config.save()

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
                    surface_type = BucketTypes.HARDENED_SURFACE
                elif name.find('gedraineerd') >= 0:
                    surface_type = BucketTypes.DRAINED_SURFACE
                else:
                    print 'WARNING: bucket type "%s"unknown, take drained'%name
                    surface_type = BucketTypes.DRAINED_SURFACE

            else:
                #single bucket
                print 'single bucket: %s'%sheet.cell(35, colnr).value
                col_upper = colnr
                col_lower = colnr

                name = sheet.cell(35, col_upper).value

                if name.find('stedelijk') >= 0:
                    bucket.surface_type = BucketTypes.STEDELIJK_SURFACE
                elif name.find('ongedraineerd') >= 0:
                    bucket.surface_type = BucketTypes.UNDRAINED_SURFACE
                elif name.lower().find('verhard') >= 0:
                    bucket.surface_type = BucketTypes.HARDENED_SURFACE
                elif name.lower().find('landelijk') >= 0:
                    bucket.surface_type = BucketTypes.UNDRAINED_SURFACE
                else:
                    print 'WARNING: bucket type "%s" unknown, take undrained'%name
                    bucket.surface_type = BucketTypes.UNDRAINED_SURFACE

            if Bucket.objects.filter(open_water=open_water, name=name, surface_type=surface_type).count()>0:
                bucket = Bucket.objects.filter(open_water=open_water, name=name, surface_type=surface_type)[0]
            else:
                bucket = Bucket()

            bucket.name = name
            bucket.surface_type = surface_type
            bucket.slug = sheet.cell(35, col_upper).value
            bucket.surface = 0
            if not sheet.cell(43, col_upper).value in ['', None]:
                bucket.surface = sheet.cell(43, col_upper).value
            else:
                bucket.surface = 0
                print 'Warning: bucket surface veld is leeg'

            bucket.open_water = open_water

            #upper
            if bucket.surface_type == BucketTypes.HARDENED_SURFACE:
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

            #bucket.seepage
            array_with_values = [[1,1,float(sheet.cell(37+bucket_nr,1).value)]]
            parameter = pars['seepage_infiltration']
            if WaterbalanceTimeserie.objects.filter(parameter=parameter, bucket_seepage=bucket).count() == 0:
                wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(bucket.__unicode__()[:30], parameter.name[:15] ))
                bucket.seepage = wb_timeserie
            else:
                wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, bucket_seepage=bucket)[0]
            create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)

            bucket.save()
            #results

    ################# PUMPINGSTATIONS ################

    retrieve_intake_for_level_control(open_water, labels, sheet, pars)

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
    pumping_station.label = labels['uitlaat peilhandhaving']
    if type(sheet.cell(70,1).value)==type(1) or type(sheet.cell(70,1).value)==type(1.0):
        pumping_station.max_discharge = sheet.cell(70,1).value
    pumping_station.save()
    for colnr in range(4, 8):
        if (not sheet.cell(72,colnr).value == None) and len(str(sheet.cell(72,colnr).value))>0:
            name = "%s_%i"%(str(sheet.cell(72,colnr).value), colnr-3)
            print 'pomplijn voor %s op %d, %d met naam %s' % \
                 (pumping_station.__unicode__(), 72, colnr, name)
            if PumpLine.objects.filter(pumping_station=pumping_station, name=name):
                pump_line = PumpLine.objects.filter(pumping_station=pumping_station, name=name)[0]
            else:
                pump_line = PumpLine()
                pump_line.pumping_station = pumping_station
                pump_line.name = name

            parameter = pars['structure_discharge']
            if WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line).count() == 0:
                wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__()[:30], parameter.name[:15] ))
                pump_line.timeserie = wb_timeserie
            else:
                wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line)[0]
            save_timeserie_into_database(wb_timeserie, sheet, 76, 0, colnr)

            pump_line.save()

    # in- en uitlaten niet voor peilhandhaving
    inlaat_nr = 0
    uitlaat_nr = 0

    for row in range(23,31):
        if sheet.cell(row,1).value in [0] and sheet.cell(row,2).value in [0]:
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
                uitlaat_nr += 1
                pumping_station.label = labels["uitlaat%i"%uitlaat_nr]

            else:
                pumping_station.into = True
                inlaat_nr += 1
                pumping_station.label = labels["inlaat%i"%inlaat_nr]

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

            colnr = row - 13
            # as row in range(23, 31), colnr in range(10, 18)
            if (not sheet.cell(72,colnr).value == None) and len(str(sheet.cell(72,colnr).value))>0:
                name = "%s_%i"%(str(sheet.cell(72,colnr).value), colnr-3)
                print 'opgedrukte pomplijn voor %s op rij %d, kolom %d met naam %s' % \
                     (pumping_station.__unicode__(), 72, colnr, name)
                if PumpLine.objects.filter(pumping_station=pumping_station, name=name):
                    pump_line = PumpLine.objects.filter(pumping_station=pumping_station, name=name)[0]
                else:
                    pump_line = PumpLine()
                    pump_line.pumping_station = pumping_station
                    pump_line.name = name

                parameter = pars['structure_discharge']
                if WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line).count() == 0:
                    wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__()[:30], parameter.name[:15] ))
                    pump_line.timeserie = wb_timeserie
                else:
                    wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line)[0]
                save_timeserie_into_database(wb_timeserie, sheet, 76, 0, colnr)

                pump_line.save()
            else:
                print 'opgedrukte jaarlijkse tijdreeks voor %s met naam %s' % \
                      (pumping_station.__unicode__(), name)

                #discharge
                winter_value = 0
                summer_value = 1
                if not sheet.cell(row,1).value in [0, '', None]:
                    winter_value = float(sheet.cell(row,1).value)
                if not sheet.cell(row,2).value in [0, '', None]:
                    summer_value = float(sheet.cell(row,2).value)
                print row, winter_value, summer_value
                array_with_values = [[1,1,winter_value],
                                     [4,1,summer_value],
                                     [10,1,winter_value],
                                    ]
                parameter = pars['structure_discharge']
                if WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line).count() == 0:
                    wb_timeserie = WaterbalanceTimeserie.objects.create(parameter=parameter, name="%s: %s"%(pump_line.__unicode__()[:30], parameter.name[:15] ))
                    pump_line.timeserie = wb_timeserie
                else:
                    wb_timeserie = WaterbalanceTimeserie.objects.filter(parameter=parameter, pump_line_timeserie=pump_line)[0]
                create_save_yearly_timeserie_into_database(wb_timeserie, array_with_values)
                pump_line.save()


class Command(BaseCommand):
    args = "<directory_with_excelfiles>"
    help = "Load all waternet waterbalance excelfiles from a directory (only xls)."

    def handle(self, *args, **options):
        directory = str(args[0])
        load_excel_reference_results = True

        input_path = join(directory, "*.xls")

        for xls_file_name in glob.glob(input_path):
            upload_settings_from_excelfile(xls_file_name, load_excel_reference_results)




