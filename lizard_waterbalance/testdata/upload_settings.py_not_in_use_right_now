import sys
import glob
import xlrd
import os
import csv

#sys.path.append('..')
#from django.core.management import setup_environ
#import settings
#setup_environ(settings)

input_path = "c:\\wb\\*.xls"

start_year = 1996
last_year = 2012

waterbalance_area = []

teller = 0

class code_generator:
    def __init__(self):
        self.teller = {}

    def get_code(self, prefix):
        prefix = str(prefix) + "_" 
        if self.teller.has_key(prefix):
            self.teller[prefix] = self.teller[prefix] + 1
        else:
            self.teller[prefix] = 0
            
        return  str(prefix) + str(self.teller[prefix])


cgen = code_generator()

wb_area_list = []
openwater_list = []
bucket_list = []
pumping_station_list = []
pumpline_list = []

wb_timeserie_list = []
label_dict = {}
timeserie_list = []

def create_wb_timeserie(wb_ts_list, lbl_dict, code_prefix, label_name, flow_type):
    #find label
    if not lbl_dict.has_key(label_name):
        lbl_dict[label_name] = {'code': label_name,'name':label_name, 'flow_type':flow_type}

    new_wb_ts_item = {'code':cgen.get_code(code_prefix),
                      'label': lbl_dict[label_name]['code'],
                      'volume':None,
                      'chloride':None,
                      'phosphate':None,
                      'nitrate':None,
                      'sulfate':None,                      
                        }
    wb_ts_list.append(new_wb_ts_item)
    

    return new_wb_ts_item['code']



def create_yearly_timeserie(pre_code, tstype, serie):
    #tstype is which of the 5 timeseries is the one selected (volume, chloride, etc)
    code = cgen.get_code(pre_code)
    for year in range(start_year, last_year):
        for item in serie:
            timeserie_list.append([code,year,item[0],item[1],item[2]])
    for wb_ts in wb_timeserie_list:
        if wb_ts['code'] == pre_code:
            wb_ts[tstype] = code
            break
            
            

def read_timeserie(pre_code, tstype, sheet, row, date_col, value_col):
    code = cgen.get_code(pre_code)

    for rownr in range(77,5600):
        date = xlrd.xldate_as_tuple(sheet.cell(rownr,date_col).value,0)
        value = sheet.cell(rownr,value_col).value
        timeserie_list.append([code,date[0],date[1],date[2],value])

    
    for wb_ts in wb_timeserie_list:
        if wb_ts['code'] == pre_code:
            wb_ts[tstype] = code
            break    
    pass


def write_to_csv(filename, resultlist):
    output_file = open(filename,'wb')
    csv_file = csv.writer(output_file)

    if type(resultlist[0]) == type({}):
        header = resultlist[0].keys()
        csv_file.writerow(header)

        for dictorary in resultlist:
            row = []
            for field in header:
                row.append(dictorary[field])
            csv_file.writerow(row)
    else:
        for row in resultlist:
            csv_file.writerow(row)

    output_file.close()

link = "a"


for xls_file in glob.glob(input_path):
    xls = xlrd.open_workbook(xls_file)
    sheet = xls.sheet_by_name('uitgangspunten')

    ################# AREA ################
    code = cgen.get_code("A")
    wb_area = {"code":code,
                "name":sheet.cell(0,0).value,
                "slug": sheet.cell(0,0).value,
                "description":"",
                "precipitation":create_wb_timeserie(wb_timeserie_list, label_dict, code, "precipitation", 1),
                "evaporation":create_wb_timeserie(wb_timeserie_list, label_dict, code, "evaporation", 2),
                "open_water":cgen.get_code("O"),
               }
    wb_area_list.append(wb_area)

    read_timeserie(wb_area["precipitation"], "volume", sheet, 77, 0, 1)
    read_timeserie(wb_area["evaporation"], "volume", sheet, 77, 0, 2)
    

    ################# OPENWATER ################
    code = wb_area["open_water"]
    openwater = {"code":code,
                "name":"openwater",
                "surface":sheet.cell(10,3).value,
                "open_water":None,
                "indraft":None,
                "seepage":create_wb_timeserie(wb_timeserie_list, label_dict, code, "seepage", 1),
                "infiltration":create_wb_timeserie(wb_timeserie_list, label_dict, code, "infiltration", 2),
                "flow_off":None,
                "minimum_level":create_wb_timeserie(wb_timeserie_list, label_dict, code, "minimum_level", 4), #deze is eigenlijk niet type 3
                "maximum_level":create_wb_timeserie(wb_timeserie_list, label_dict, code, "maximum_level", 4), #deze is eigenlijk niet type 3
                "target_level":create_wb_timeserie(wb_timeserie_list, label_dict, code, "target_level", 4), #deze is eigenlijk niet type 3, dus 4
                "sluice_error":create_wb_timeserie(wb_timeserie_list, label_dict, code, "sluice_error", 3),
                "volume":create_wb_timeserie(wb_timeserie_list, label_dict, code, "volume", 4), #OPM: extra
              }

    openwater_list.append(openwater)
    
    create_yearly_timeserie(openwater["minimum_level"],"volume",[[1,1,sheet.cell(63,2).value],
                                                        [3,15,sheet.cell(64,2).value],
                                                        [5,1,sheet.cell(64,2).value],
                                                        [8,15,sheet.cell(65,2).value],
                                                        [10,1,sheet.cell(66,2).value],
                                                        ])

    create_yearly_timeserie(openwater["maximum_level"],"volume",[[1,1,sheet.cell(63,4).value],
                                                        [3,15,sheet.cell(64,4).value],
                                                        [5,1,sheet.cell(64,4).value],
                                                        [8,15,sheet.cell(65,4).value],
                                                        [10,1,sheet.cell(66,4).value],
                                                        ])

    if sheet.cell(64,3).ctype == 2:
        create_yearly_timeserie(openwater["target_level"],"volume",[[1,1,sheet.cell(63,3).value],
                                                            [3,15,sheet.cell(64,3).value],
                                                            [5,1,sheet.cell(64,3).value],
                                                            [8,15,sheet.cell(65,3).value],
                                                            [10,1,sheet.cell(66,3).value],
                                                            ])
    else:
        #fixed targetlevel
        create_yearly_timeserie(openwater["target_level"],"volume",[[1,1,sheet.cell(67,3).value],])


    create_yearly_timeserie(openwater["seepage"],"volume",[[1,1,sheet.cell(36,1).value],])
                                                        
    create_yearly_timeserie(openwater["infiltration"],"volume",[[1,1,sheet.cell(37,1).value],])

    #results:
    #"sluice_error" --> kolom DE in 'rekenhart'
    #Volume  --> kolom AK in 'rekenhart'
    #

    ################# BUCKETS ################
    calcsheet = xls.sheet_by_name('Rekenblad')

    
    nr = 0
    for i in range(1,15):
        if calcsheet.cell(13,i).ctype == 2 and not calcsheet.cell(13,i-1).value == calcsheet.cell(13,i).value:
            code = cgen.get_code("B")
            bucket = {"code":code,
                    "name":calcsheet.cell(0,i).value,
                    "surface":calcsheet.cell(1,i).value,
                    "open_water":openwater["code"],
                    "indraft":create_wb_timeserie(wb_timeserie_list, label_dict, code, "indraft", 2),
                    "uitspoel":create_wb_timeserie(wb_timeserie_list, label_dict, code, "uitspoel", 1),#deze kon ik ook niet vinden, flow_off is surface of niet?
                    "seepage":create_wb_timeserie(wb_timeserie_list, label_dict, code, "seepage", 1),
                    "infiltration":create_wb_timeserie(wb_timeserie_list, label_dict, code, "infiltration", 2),
                    "flow_off":create_wb_timeserie(wb_timeserie_list, label_dict, code, "flow_off", 2),
                    "computed_flow_off":"", #OPM: waar is deze voor???
                    #OPM: velden hieronder zijn nieuw, not yet in model. Veld namen naar omschrijving
                    "bl gewasverdampingsfactor (-)":calcsheet.cell(4,i).value,
                    "bl min. Gewasverdampingsfactor (-)":calcsheet.cell(5,i).value,
                    "bl f_uitpoel":calcsheet.cell(6,i).value,
                    "bl f_intrek":calcsheet.cell(7,i).value,
                    "bl porositeit / bergingsruimte":calcsheet.cell(8,i).value,
                    "bl max level":calcsheet.cell(9,i).value,
                    "bl equilibrium level":calcsheet.cell(10,i).value,
                    "bl minimum level":calcsheet.cell(11,i).value,
                    "bl init level":calcsheet.cell(12,i).value,
                    "ol gewasverdampingsfactor (-)":None,
                    "ol min. Gewasverdampingsfactor (-)":None,
                    "ol f_uitpoel":None,
                    "ol f_intrek":None,
                    "ol porositeit / bergingsruimte":None,
                    "ol max level":None,
                    "ol equilibrium level":None,
                    "ol minimum level":None,
                    "ol init level":None,
                    "bl_volume":create_wb_timeserie(wb_timeserie_list, label_dict, code, "volume", 4),
                    "ol_volume":None,
                      }
                  
            bucket["nr"] = i
                                                           
            if calcsheet.cell(13,i).value == calcsheet.cell(13,i+1).value:
                #new, not yet in model (boven laag)
                bucket["ol gewasverdampingsfactor (-)"] = calcsheet.cell(4,i+1).value
                bucket["ol min. Gewasverdampingsfactor (-)"] = calcsheet.cell(5,i+1).value
                bucket["ol f_uitpoel"] = calcsheet.cell(6,i+1).value
                bucket["ol f_intrek"] = calcsheet.cell(7,i+1).value
                bucket["ol porositeit / bergingsruimte"] = calcsheet.cell(8,i+1).value
                bucket["ol max level"] = calcsheet.cell(9,i+1).value
                bucket["ol equilibrium level"] = calcsheet.cell(10,i+1).value
                bucket["ol minimum level"] = calcsheet.cell(11,i+1).value
                bucket["ol init level"] = calcsheet.cell(12,i+1).value
                bucket["ol_volume"] = create_wb_timeserie(wb_timeserie_list, label_dict, code, "volume", 4),
                seepage_col = i+1
                two_layers = True
            else:
                seepage_col = i
                two_layers = False

            if calcsheet.cell(3,seepage_col).value > 0:
                create_yearly_timeserie(openwater["seepage"],"volume",[[1,1,calcsheet.cell(3,seepage_col).value],])
                create_yearly_timeserie(openwater["infiltration"],"volume",[[1,1,0],])
            else:
                create_yearly_timeserie(openwater["seepage"],"volume",[[1,1,0],])
                create_yearly_timeserie(openwater["infiltration"],"volume",[[1,1,-1*calcsheet.cell(3,seepage_col).value],])


            """
            "Results" --> 
            "indraft" --> Rekenblad, 14e kolom per bakje
            "flow_off"  --> Rekenblad, 7e kolom per bakje
            "uitspoeling --> Rekenblad, 13e kolom per bakje
            "volume --> Rekenblad, 6e kolom per bakje
            """
            bucket_list.append(bucket)

    ################# PUMPINGSTATIONS ################

    randen_sheet = xls.sheet_by_name('RANDEN')
    
    for i in range(23,32):
        active = False

        if sheet.cell(i,1).ctype == 2 and sheet.cell(i,1).value > 0:
            active = True
            calculated = False
            timeserie = False
        elif sheet.cell(i,1).ctype == 1 and sheet.cell(i,1).value == "ts":
            active = True
            calculated = False                    
            timeserie = False
        elif sheet.cell(i,1).ctype == 1 and sheet.cell(i,1).value == "rekenhart":
            active = True
            calculated = True                    
            timeserie = False

        
        if i < 29:
            into = True
        else:
            into = False

        if active:
            pumping_station = {"code":cgen.get_code("PS"),
                "name":sheet.cell(i,0).value,
                "open_water":openwater["code"],
                "into":into,
                "percentage":100, #veld wordt nog niet goed ingevuld
                "calculated":calculated #nieuw veld die aangeeft of het kunstwerk berekend wordt of opgedrukt
              }

            pumping_station_list.append(pumping_station)

            code = cgen.get_code(pumping_station['code'])

            if calculated == False:
                ts = create_wb_timeserie(wb_timeserie_list, label_dict, code, "pumptimeserie", into)
                ts_ref = None
            else :
                ts = create_wb_timeserie(wb_timeserie_list, label_dict, code, "calculated pump timeserie", into)
                ts_ref = create_wb_timeserie(wb_timeserie_list, label_dict, code, "reference pump timeserie", into)

            #vooralsnog wordt er uitgegaan van 1 pomplijn
            pump_line = {"code":code,
                "pump":pumping_station['code'],
                "timeserie":ts,
                "ref_timeserie":ts_ref #extra timeserie
            }

            pumpline_list.append(pump_line)

            if calculated == False and timeserie == False:

                create_yearly_timeserie(pump_line["timeserie"],"volume",[[1,1,sheet.cell(i,1).value],
                                                    [4,1,sheet.cell(i,1).value],
                                                    [10,1,sheet.cell(i,2).value],
                                                    ])

            elif calculated == False and timeserie == True:

                pass
                #read_timeserie(pump_line["timeserie"], randen_sheet, 13, 0, i-17)
                                        
            elif calculated == True and timeserie == True:

                pass
                #read_timeserie(pump_line["timeserie"], randen_sheet, 13, 0, i-17)

                pass

write_to_csv('wb_area.csv',wb_area_list)
write_to_csv('openwater.csv',openwater_list)
write_to_csv('bucket.csv',bucket_list)
write_to_csv('wb_timeseries.csv',wb_timeserie_list)
write_to_csv('timeserie.csv',timeserie_list)

write_to_csv('pumpingstation.csv',pumping_station_list)
write_to_csv('pumpline.csv',pumpline_list)

#berekende uitlaat staat niet in het lijstje
                                        
            
                




"""                                                       

wb_timeserie = {"code":"label",
            "label":"",
            "volume":openwater["code"],
            "chloride":"",
            "phosphate":"",
            "nitrate":"",
            "sulfate":"",
          }




"""



