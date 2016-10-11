#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import scipy.io as spio
import datetime
import sys
from traits.api \
    import HasTraits, Instance, Str, on_trait_change
from traitsui.api \
    import View, VGroup, Item, ValueEditor, TextEditor
from copy import deepcopy
import sweg_vs_main as main

class DictEditor(HasTraits):
    SearchTerm = Str()
    Object = Instance( object )

    def __init__(self, obj, **traits):
        super(DictEditor, self).__init__(**traits)
        self._original_object = obj
        self.Object = self._filter(obj)

    def trait_view(self, name=None, view_elements=None):
        return View(
          VGroup(
            Item( 'SearchTerm',
                  label      = 'Search:',
                  id         = 'search',
                  editor     = TextEditor(),
                  #style      = 'custom',
                  dock       = 'horizontal',
                  show_label = True
            ),
            Item( 'Object',
                  label      = 'Debug',
                  id         = 'debug',
                  editor     = ValueEditor(),
                  style      = 'custom',
                  dock       = 'horizontal',
                  show_label = False
            ),
          ),
          title     = 'Dictionary Editor',
          width     = 800,
          height    = 600,
          resizable = True,
        )

    @on_trait_change("SearchTerm")
    def search(self):
        self.Object = self._filter(self._original_object, self.SearchTerm)

    def _filter(self, object_, search_term=None):
        def has_matching_leaf(obj):
            if isinstance(obj, list):
                return any(
                        map(has_matching_leaf, obj))
            if isinstance(obj, dict):
                return any(
                        map(has_matching_leaf, obj.values()))
            else:
                try:
                    if not str(obj) == search_term:
                        return False
                    return True
                except ValueError:
                    False

        obj = deepcopy(object_)
        if search_term is None:
            return obj

        if isinstance(obj, dict):
            for k in obj.keys():
                if not has_matching_leaf(obj[k]):
                    del obj[k]

            for k in obj.keys():
                if isinstance(obj, dict):
                    obj[k] = self._filter(obj[k], search_term)
                elif isinstance(obj, list):
                    filter(has_matching_leaf,obj[k])

        return obj
        
def replace_forbidden_characters(dict_init, dict_char_replace):
    '''replaces umlaute with self-defined replacement.'''
    for umlaut, replacement in dict_char_replace.iteritems():
        if umlaut in dict_init[
                'i_dict_boundary']['dict_boundary_geodb']['str_geom_name']:
            dict_init['i_dict_boundary']['dict_boundary_geodb']['str_geom_name'] = \
              dict_init['i_dict_boundary']['dict_boundary_geodb'][
                'str_geom_name'].replace(umlaut, replacement)
    return dict_init
    
'''
when configuring a new simulation, take heed of the following order:
1. specify the geographic boundary in i_dict_boundary_geodb
2. specify the temporal conditions in i_dict_dates
3. specify the register data in i_dict_register_info, 
   dont't forget to assign an additional register_name
3. specify the weather dataset in i_str_weather_dataset
4. specify the methods for windspeed correction in i_dict_windspeed_corr
5. specify whether and which random input is to be used in i_dict_random_input
6. specify output procedure in i_dict_result_output_variable and 
   i_dict_result_output_database
7. specify multiprocessing functionality in ctrl_bol_multiprocessing
'''
        
#specify simulation parameters
dict_init = {
    'i_str_info': "SWEG VS initialization variable",
     #source: GeoDB, Shapefile, DBtable
     #str_geom_adminlvl -> Land, Bundesland, Regierungsbezirk, 
     #Kreis, Verwaltungsgemeinschaft, Gemeinde
     'i_dict_boundary': {
         'source': 'GeoDB',
         'str_shp_filepath': "",
         'dict_boundary_geodb': {
             'str_schema': "deutschland", 
             'str_data': "geb01_f", 
             'str_geom_adminlvl': "Bundesland", 
             'str_geom_name': "Brandenburg", 
             'str_geom_column': "geom"
         },
         'dict_boundary_dbtable': {
             'str_schema': "deutschland", 
             'str_data': "tso_wgs84", 
             'str_condition_col': 'tso',
             'str_condition_val': "50 Hertz",
             'str_geom_column': "geom"
         }
     },
     'i_int_max_runtime_wec': 20,
     'i_dict_performance_curves_info': {
         'cp_curves':{
             'str_schema':"ee_komponenten", 
             'str_data':"wea_cpcurves"
         }, 
         'power_curves':{
             'str_schema':"ee_komponenten", 
             'str_data':"wea_powercurves_all"
         }
     },
     #register_name = short name for register that is used 
     #to name tables in database export'''
     'i_dict_register_info': {
         'str_schema':"", 
         'str_data':"", 
         'register_name': ""
     },
     #i_str_weather_dataset = COSMO-DE or ANEMOS
     'i_str_weather_dataset':"COSMO-DE",
     #arr_date_period [start, end],
     #year of start and end should always be the same! 
     #start <= timeperiod <= end'''
     'i_dict_dates': {
     'str_date_format': "yyyy-mm-dd", 
     'arr_date_period': ['2011-01-01', '2011-12-31']
     },
     #height_corr: linear, logarithmic; 
     #density_corr: IEC_2006 (= constant efficiency), WindPro_2010 (= windspeed dependent efficiency)
     #Source WindPro_2010: http://help.emd.dk/knowledgebase/content/ReferenceManual/PowerCurveOptions.pdf
     #Anemos only logarithmic height_corr!
     'i_dict_windspeed_corr': {
         'height_corr': "linear", 
         'density_corr': "WindPro_2010"
     },
     'i_dict_random_input': {
         'bol_save': 0, 
         'str_save_path': "",
         'bol_load': 1, 
         'str_load_path': ""
     },
     'i_result_postprocessing': {
         'method': [''],
         'flh_setup': {
             'wind_index': 102,
             'flh_min_mean_max': [500, 1860, 3000],
             'flh_mean_range': [0.85, 1.2],
             'flh_shares': {
                 'Berlin': [1, 1.5, 0.91], 
                 'Brandenburg': [1, 0.89, 1.01],
                 'Mecklenburg-Vorpommern': [1, 0.89, 0.9],
                 'Sachsen': [1, 0.81, 1], 
                 'Sachsen-Anhalt': [1, 0.90, 0.91], 
                 'Thüringen': [1, 0.87, 0.91],
                 'Hamburg': [1, 0.8, 0.86]
             }
         }
     },
     #cumulative results: sum of "availability",  "Power_100", "Energy_100", "Power_real", "Energy_real"
     #cumulation_level_space: "Boundary" or "Land" or "Bundesland" or "Kreis" or "Gemeinde" or "Windpark"; ["Boundary", "Land", "Bundesland", "Kreis", "Gemeinde", "Windpark"], only include cumulation_level_space Boundary when no respective admin_level exists and admin level of same size or smaller, eg. for Brandenburg do not include Land, for landkreis do not include Land and Bundesland
     #cumulation_level_time: "None", "Hour", "Day" or "Period", use "Hour" only if detailed results have higher timely resolution
     #timeseries_format: "original" or "normalized"
     #if interval_minutes = 60 and cumulation_level_time = Hour, you need to specify ctrl_dict_individual_results in order to get any output!
     'ctrl_dict_cumulative_results': {
         'cumulation_level_space': ["Windpark"], 
         'cumulation_level_time': "Period",
         'timeseries_format': "original"
     },
     'ctrl_dict_console_output': {
         'bol_console_output': 1, 
         'int_console_details': 1
     },
     #output variables: ["availability",  "power_100", "energy_100", "power_real", "energy_real", "operation_hours", "flh_factor"]
     'i_dict_result_output_database':{
         'bol_database_output': 1, 
         'str_schema': "sweg_vs", 
         'str_table_result_info': "result_info", 
         'existing_data': "drop",
         'output_variables': ["availability",  "power_100", "energy_100", "power_real", "energy_real", "operation_hours", "flh_factor"]
     },
     'ctrl_bol_multiprocessing': {
         'enabled': 1, 
         'nr_of_processors': 6
     }
}

#1st option for simulation start:
#run simulation directly with dict_init as first parameter  
dict_return = main.sweg_vs_main(dict_init)

#2nd option for simulation start:
#a) replace forbidden characters with unicode
#dict_init = replace_forbidden_characters(
  #dict_init, 
  #{"Ä":"Auml", "ä":"auml", "Ö":"Ouml", "ö":"ouml", "Ü":"Uuml", "ü":"uuml"})
#b) save dict_init to file init.mat
#try:
    #spio.savemat('init.mat', dict_init, oned_as = 'row')
    
    #print 'Initialization file SWEG_VS_init.mat was created!'
#except:
    #print 'An error occured: ' + str(sys.exc_info())

#c) run simulation with path to init.mat as first parameter
#dict_return = main.sweg_vs_main(
#  "<path to /init.mat>", 
#  {"Ä":"Auml", "ä":"auml", "Ö":"Ouml", "ö":"ouml", "Ü":"Uuml", "ü":"uuml"}
#)

#return visual representation of returned dictionary
#b = DictEditor(dict_return)
#b.configure_traits()
