#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Script for the generation of an init.mat file as the basis for the SWEG VS simulation module
'''

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
dict_init = {'i_str_info': "SWEG VS initialization variable",
             'i_str_date': str(datetime.datetime.now().replace(microsecond=0)),
             'i_dict_db_connect': {
                 'database': "reiners_db", 
                 'host': "192.168.10.25", 
                 'user': "sweg", 
                 'password': "vs2013"
             },
             #source: "GeoDB", "Shapefile", or "DBtable"
             #str_geom_adminlvl: "Land", "Bundesland", "Regierungsbezirk", 
             #"Kreis", "Verwaltungsgemeinschaft", "Gemeinde"
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
                     'str_condition_col': "tso",
                     'str_condition_val': "50 Hertz",
                     'str_geom_column': "geom"
                }
             },
             #register_name = short name for register that is used 
             #to name tables in database export
             'i_dict_register_info': {
                 'str_schema': "deutschland", 
                 'str_data':"", 
                 'register_name': ""
             },
             #i_int_max_runtime_wec = maximum runtime of 
             #wind energy converters in years
             'i_int_max_runtime_wec': 20,
             'i_dict_performance_curves_info': {
                 'cp_curves':{
                     'str_schema':"ee_komponenten", 
                     'str_data': "wea_cpcurves"
                 }, 
                 'power_curves':{
                     'str_schema': "ee_komponenten", 
                     'str_data': "wea_powercurves_all"
                 }
             },
             #method: "average" or "weighted_average"
             'i_dict_powercurve_mix': {
                 'method': "weighted_average",
                 'source': {
                     'str_schema': "ee_komponenten",
                     'str_data': "wea_anlagentypen_share_summary",
                     'arr_structure': [
                       "rli_anlagen_id", "year_2009",  "year_2010",  
                       "year_2011",  "year_2012", 
                     ]
                 }
             },
             #i_str_weather_dataset: "COSMO-DE" or "ANEMOS"
             'i_str_weather_dataset': "ANEMOS",
             #str_base_path ending with '/'
             'i_dict_weather_dataset_info': {
                 'COSMO-DE': {
                     'interval_minutes': 60, 
                     'str_base_path': "",
                     'power_curve_factor': 1.12
                 }, 
                 'ANEMOS':{
                     'interval_minutes': 60, 
                     'str_base_path': "",
                     'str_path_prefix_windspeed': "Zeitreihen_Windgeschwindigkeit_", 
                     'str_path_prefix_temperature': "Zeitreihen_Temperatur_",
                     'power_curve_factor': 1.05
                 }
             },
             'i_dict_weather_grid_info':{
                 'COSMO-DE':{
                     'str_schema': "deutschland", 
                     'str_data': "cosmo_de_polygongitter", 
                     'str_geom_column': "geom_poly"
                 },
                 'ANEMOS': {
                     'str_schema': "deutschland", 
                     'str_data': "anemos_polygongitter", 
                     'str_geom_column': "geom_poly"
                 }
             },
             #arr_date_period: ["<start>", "<end>"],
             #year of start and end should always be the same! 
             #<"start"> <= timeperiod <= <"end">
             'i_dict_dates': {
                 'str_date_format': "yyyy-mm-dd", 
                 'arr_date_period': ['2010-01-01', '2010-12-31']
             },
             #height_corr: "linear" or "logarithmic" 
             #density_corr: IEC_2006 (= constant efficiency), WindPro_2010 (= windspeed dependent efficiency)
             #Source WindPro_2010: http://help.emd.dk/knowledgebase/content/ReferenceManual/PowerCurveOptions.pdf
             #Anemos only logarithmic height_corr!
             'i_dict_windspeed_corr': {
                 'height_corr': "logarithmic", 
                 'density_corr': "WindPro_2010"
             },
             #method: "constant" = constant value 'constant' for wind farm efficiency, 
             #method: "ideal_square_simple" = wind farm efficiency dependent on 
             #number of turbines based on square layout of wind farm
             #v_dependency: "linear_1-min_eff-1" or "linear_min_eff-min_eff-1"
             'i_dict_windfarm_efficiencies': {
                 'method':"ideal_square_simple", 
                 'v_dependency': {
                     'method': "linear_min_eff-min_eff-1",
                     'factor': 2
                 },
                 'constant': 0.9, 
                 'ideal_square_simple': {
                     'min_efficiencies': [
                         [1,2,3,4,9,16,25,36,49],
                         [1.0,1.0,1.0,0.825,0.762,0.724, 0.697, 0.677, 0.661]
                     ], 
                     'factor': 1.1,
                     'min_info': [
                         ["nr_of_turbines"],["min_windfarm_efficiency"]
                     ]
                 }
             },
             'i_dict_non_availabilities': {
                 'technical': {
                     'Component': ["Drive Train", "Supporting Structure", 
                                   "Generator", "Gearbox", "Rotor Blades", 
                                   "Mechanical Brake", "Rotor Hub", 
                                   "Yaw System", "Hydraulic System", 
                                   "Sensors", "Electronic Control", 
                                   "Electrical System"], 
                     'FailureRate': [0.055, 0.092, 
                                     0.100, 0.107, 0.115, 
                                     0.132, 0.173, 
                                     0.181, 0.229, 
                                     0.246, 0.406, 
                                     0.553], 
                     'DowntimeHours':[126, 80, 
                                      179, 162, 82, 
                                      65, 100, 
                                      61, 28, 
                                      37, 45, 
                                      36]}, 
                 'misc':{
                     'Frequency': 100, 
                     'Rate': 1.0, 
                     'DowntimeHours': 3
                 }
             },
             #method: full_load_hours
              'i_result_postprocessing': {
                 'method': ["full_load_hours"],
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
             'i_dict_z0_info': {
                 'str_schema': "deutschland", 
                 'str_data': "cosmo_de_z0_view"
             },
             #i_dict_random_input contains info whether randomly generated data 
             #will be stored and can be loaded for scenario simulations to keep boundary conditions equal
             #if 'bol_load':True and no data exists, availability data will be generated on first run
             'i_dict_random_input': {
                 'bol_save': False, 
                 'str_save_path': "",
                 'bol_load': False, 
                 'str_load_path': ""
             },
             #i_dict_result_output = define how result is returned 
             'i_dict_result_output_variable': True, 
             #existing_tables: "drop", "delete" or "update"
             #output variables: ["availability",  "power_100", "energy_100", "power_real", "energy_real", "operation_hours", "flh_factor", "power_curve"]
             'i_dict_result_output_database':{
                     'bol_database_output': 1, 
                     'str_schema': "sweg_vs", 
                     'str_table_result_info': "result_info", 
                     'existing_data': "drop",
                     'output_variables': ["availability",  "power_100", "energy_100", "power_real", "energy_real", "operation_hours", "flh_factor"] 
             },
             #output of mat file is not yet implemented. Problem with 
             #older mat versions and the rather extensive implementation of 
             #hdf file building
             'i_dict_result_output_mat':{
                 'bol_mat_output': False, 
                 'str_mat_output_path': ""
             },
             #if chart_per_grid_cell = True, specify: 'ctrl_dict_individual_results': ["availability","windfarm_efficiency", "EPF", "cp", "P", "rho", "v", "Power_100", "Power_100_spec", "Power_real", "Power_real_spec", "Power_loss"],
             'ctrl_dict_charts': {
                 'chart_per_windfarm': False, 
                 'chart_per_grid_cell': False
             },
             #available individual variables: ["availability", "windfarm_efficiency", "EPF", "cp", "P", "rho", "v", "Power_100", "Power_100_spec", "Power_real", "Power_real_spec", "Power_loss"]
             'ctrl_dict_individual_results': [""],
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
             'ctrl_dict_logging': {
                 'bol_logging': False, 
                 'str_logfile_path': "Path"
             },
             #int_console_details -> 1 = main info,2 =  + intermediate steps or 3 =  + intermediate values, define how many details are printed to the console
             'ctrl_dict_console_output': {
                 'bol_console_output': True, 
                 'int_console_details': 1
             },
             'ctrl_bol_multiprocessing': {
                 'enabled': True, 
                 'nr_of_processors': 4
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
    

