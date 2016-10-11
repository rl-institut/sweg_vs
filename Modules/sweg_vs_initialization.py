#!/usr/bin/python
# -*- coding: utf-8 -*-

def sweg_vs_initialization(init, dict_char_replace, time_start):
    '''
    Loads the init variable and prepares variables for simulation run.
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin
    
    Keyword arguments.
    
    init -- variable containing either path to .mat initialization file or 
            initialization variable of type dictionary   
            
    dict_char_replace -- dictionary containing umlaute and their replacement
    
    time_start -- timestamp of simulation run start
    '''    
    #import additional modules
    import time
    import datetime
    import psycopg2
    import sys
    
    from Modules.sweg_vs_additional_modules import convert_date
    from Modules.sweg_vs_additional_modules import console_info as Info
    from Modules.sweg_vs_additional_modules import loadmat
    
    #define local functions
        
    def restore_forbidden_characters(dict_init, dict_char_replace):
        '''Restore Umlaute according to translation dictionary.'''
        for umlaut, replacement in dict_char_replace.iteritems():
            if replacement in \
                    dict_init['i_dict_boundary']['dict_boundary_geodb'][
                      'str_geom_name']:
                dict_init['i_dict_boundary']['dict_boundary_geodb'][
                  'str_geom_name'] = \
                  dict_init['i_dict_boundary']['dict_boundary_geodb'] \
                    ['str_geom_name'].replace(replacement, umlaut)
        return dict_init
        
    #declare local variables
    arr_error = []
    bol_loadmat_error = True
    int_loadmat_count = 0
    conn_rli_db = None
    cur_rli_db = None
    dict_init = {}
    arr_timestamp = []
    
    if init != None:    
        #check for input data type
        if isinstance(init, str) == True:
            #input is regarded as path
            while bol_loadmat_error == True:
                bol_loadmat_error = False
                try:
                    #load initialization file and 
                    #assign contents to variable dict_init
                    dict_init = loadmat(init)
                    dict_init = restore_forbidden_characters(
                      dict_init, dict_char_replace)
                    dict_console_info = {
                      'time_start':time_start, 
                      'ctrl_bol_console_output': dict_init[
                        'ctrl_dict_console_output']['bol_console_output'], 
                      'ctrl_int_console_details': dict_init[
                        'ctrl_dict_console_output']['int_console_details']
                    }
                    Info('''Initialization file loaded,
                      forbidden characters restored''', 2, dict_console_info)
                except:
                    bol_loadmat_error = True
                    int_loadmat_count += 1
                if int_loadmat_count != 0:
                    Info("Waiting 10 seconds, then retry. " + \
                    str(int_loadmat_count)+ "/3",1,dict_console_info)
                    time.sleep(2)
                    if int_loadmat_count == 2:
                        arr_error.append(
                          'Error! Initialization file could not be loaded: ' +\
                          str(sys.exc_info()))
                        break
            if bol_loadmat_error == True:
                return arr_error, conn_rli_db, cur_rli_db, dict_init
                
        elif isinstance(init, dict) == True:
            #input is regarded as dict
            dict_init = init
            if dict_init['i_str_info'] != "SWEG VS initialization variable":
                arr_error.append(
                  '''Error! Metadata of initialization variable does not match
                  condition "SWEG VS initialization variable"'''
                )
                return arr_error, conn_rli_db, cur_rli_db, dict_init
        else:
            #input error
            arr_error.append('''Error! Input parameter in SWEG_VS_main is
              neither path to initialization file nor initialization
              variable of type dictionary.'''
            )
            return arr_error, conn_rli_db, cur_rli_db, dict_init 
            
        #extract boundary info
        if dict_init['i_dict_boundary']['source'] == 'GeoDB':
            str_boundary = \
              dict_init['i_dict_boundary']['dict_boundary_geodb'][
                'str_geom_name'] + "_"
            
        elif dict_init['i_dict_boundary']['source'] == 'Shapefile':
            #find start and stop positions of shapefile name
            start = len(
              dict_init['i_dict_boundary']['str_shp_filepath']) - \
              dict_init['i_dict_boundary']['str_shp_filepath'][::-1].index('/')
            stop = len(
              dict_init['i_dict_boundary']['str_shp_filepath']) - \
              dict_init['i_dict_boundary']['str_shp_filepath'][::-1].index('.') - 1
            str_boundary = dict_init[
              'i_dict_boundary']['str_shp_filepath'][start:stop] + "_"
        elif dict_init['i_dict_boundary']['source'] == 'DBtable':
            str_boundary = dict_init['i_dict_boundary'][
              'dict_boundary_dbtable']['str_condition_val']
        else:
            str_boundary = ""
            
        #adapt data types, if necessary
            
        if 'i_dict_dates' not in dict_init:
            arr_error.append('Error! No calculation period input specified.')
        else:
            if 'str_date_format' not in dict_init['i_dict_dates']:
                dict_init['i_dict_dates']['str_date_format'] = "yyyy-mm-dd"
        
            #adapt data type of i_dict_dates
            if isinstance(init, dict) != True:
                dict_init['i_dict_dates']['arr_date_period'] = dict_init[
                  'i_dict_dates']['arr_date_period'].tolist()
              
            dict_init['i_dict_dates']['arr_date_period'][0] = convert_date(
              dict_init['i_dict_dates']['str_date_format'], 
              dict_init['i_dict_dates']['arr_date_period'][0])
              
            dict_init['i_dict_dates']['arr_date_period'][1] = convert_date(
              dict_init['i_dict_dates']['str_date_format'], 
              dict_init['i_dict_dates']['arr_date_period'][1])
              
            if dict_init['i_dict_dates']['arr_date_period'][0].year != \
                    dict_init['i_dict_dates']['arr_date_period'][1].year:
                arr_error.append('Error! Calculation Period is max one year.')
        
        
        #check for existence of default variables, if false, set default          
        if 'i_str_date' not in dict_init:
            dict_init['i_str_date'] = \
                str(datetime.datetime.now().replace(microsecond=0))
                
        if 'i_dict_db_connect' not in dict_init:
            dict_init['i_dict_db_connect'] = {
                 'database': "reiners_db", 
                 'host': "192.168.10.25", 
                 'user':"sweg", 
                 'password':"vs2013"
            }
             
        if 'i_dict_boundary' not in dict_init: 
            dict_init['i_dict_boundary'] = {
                 'source': ''
            }

                
       
        if 'i_dict_register_info' not in dict_init:
            arr_error.append('Error! No installation register input specified.')
            
        if 'i_int_max_runtime_wec' not in dict_init:
            dict_init['i_int_max_runtime_wec'] = 20
        
        if 'i_dict_performance_curves_info' not in dict_init:
            dict_init['i_dict_performance_curves_info'] = {
                 'cp_curves':{
                     'str_schema': "ee_komponenten", 
                     'str_data': "wea_cpcurves"
                 }, 
                 'power_curves':{
                     'str_schema': "ee_komponenten", 
                     'str_data': "wea_powercurves_all"
                 }
            }
            
        if 'i_dict_powercurve_mix' not in dict_init:
            dict_init['i_dict_powercurve_mix'] = {
                 'method': "average"
            }
        
        if 'i_str_weather_dataset' not in dict_init:
            arr_error.append('Error! No weather data set input specified.')
            
        if 'i_dict_weather_dataset_info' not in dict_init:
            dict_init['i_dict_weather_dataset_info'] = {
                 'COSMO-DE': {
                     'interval_minutes': 60, 
                     'str_base_path':"/home/likewise-open/RL-INSTITUT/marcus.biank/rli-data1/Cosmo_DE_out/",
                     #'power_curve_factor': 1.12
                     'power_curve_factor': 1.0
                 }, 
                 'ANEMOS':{
                     'interval_minutes': 60, 
                     'str_base_path':"/home/likewise-open/RL-INSTITUT/marcus.biank/rli-data/Originaldaten/Anemos/",
                     'str_path_prefix_windspeed': "Zeitreihen_Windgeschwindigkeit_", 
                     'str_path_prefix_temperature': "Zeitreihen_Temperatur_",
                     'power_curve_factor': 1.05
                 }
             }
        
        if 'i_dict_weather_grid_info' not in dict_init:
            dict_init['i_dict_weather_grid_info'] = {
                 'COSMO-DE':{
                     'str_schema':"deutschland", 
                     'str_data':"cosmo_de_polygongitter", 
                     'str_geom_column': 'geom_poly'
                 },
                 'ANEMOS': {
                     'str_schema':"deutschland", 
                     'str_data':"anemos_polygongitter", 
                     'str_geom_column': "geom_poly"
                 }
            }
        
        if 'i_dict_windspeed_corr' not in dict_init:
            dict_init['i_dict_windspeed_corr'] = {
                 'height_corr': "linear", 
                 'density_corr': "WindPro_2010"
            }
        
        if 'i_dict_windfarm_efficiencies' not in dict_init:
            dict_init['i_dict_windfarm_efficiencies'] = {
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
            }
        if 'i_dict_non_availabilities' not in dict_init:
            dict_init['i_dict_non_availabilities'] = {
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
            }
            
        if 'i_result_postprocessing' not in dict_init:
            dict_init['i_result_postprocessing'] = {
                 'method': ['']
            }
            
        if 'i_dict_z0_info' not in dict_init:
            dict_init['i_dict_z0_info'] = {
                 'str_schema':"deutschland", 
                 'str_data':"cosmo_de_z0_view"
            }
        
        if 'i_dict_random_input' not in dict_init:
            dict_init['i_dict_random_input'] = {
                 'bol_save': 0, 
                 'bol_load': 0
            }
            
        if 'i_dict_result_output_variable' not in dict_init:
            dict_init['i_dict_result_output_variable'] = 1
            
        if 'i_dict_result_output_database' not in dict_init:
            dict_init['i_dict_result_output_database'] = {
                 'bol_database_output': 0
            }
            
        if 'i_dict_result_output_mat' not in dict_init:
            dict_init['i_dict_result_output_mat'] = {
                 'bol_mat_output': 0
            }
               
        if 'ctrl_dict_charts' not in dict_init:
            dict_init['ctrl_dict_charts'] = {
                 'chart_per_windfarm': 0, 
                 'chart_per_grid_cell': 0
            }  
             
        if 'ctrl_dict_individual_results' not in dict_init:
            dict_init['ctrl_dict_individual_results'] = [""]
            
        if 'ctrl_dict_cumulative_results' not in dict_init:
            dict_init['ctrl_dict_cumulative_results'] = {
                 'cumulation_level_space': ["Boundary"], 
                 'cumulation_level_time': "Period",
                 'timeseries_format': "original"
            }
            
        if 'ctrl_dict_logging' not in dict_init:
            dict_init['ctrl_dict_logging'] = {
                 'bol_logging': 0
            }
            
        if 'ctrl_dict_console_output' not in dict_init:
            dict_init['ctrl_dict_console_output'] = {
                 'bol_console_output': 1, 
                 'int_console_details': 1
            }
        dict_console_info = {
          'time_start':time_start, 
          'ctrl_bol_console_output': dict_init[
            'ctrl_dict_console_output']['bol_console_output'], 
          'ctrl_int_console_details': dict_init[
            'ctrl_dict_console_output']['int_console_details']
        } 
    
        if 'ctrl_bol_multiprocessing' not in dict_init:
            dict_init['ctrl_bol_multiprocessing'] = {
                 'enabled': 0
            }
             
        #check variables for plausibility and range/value violation of values
        if 'database' not in dict_init['i_dict_db_connect'] and \
                'host' not in dict_init['i_dict_db_connect'] and \
                'user' not in dict_init['i_dict_db_connect'] and \
                'password' not in dict_init['i_dict_db_connect']:
            arr_error.append('Error! Database connection info not sufficient')
            
        if len(dict_init['i_dict_register_info']['register_name']) > 15 and\
                dict_init['i_dict_result_output_database'][
                  'bol_database_output'] == True:
            arr_error.append('Error! Short register name is too long!')
            
        if dict_init['i_dict_weather_dataset_info'][
                dict_init['i_str_weather_dataset']]['str_base_path'][-1] != '/':
            dict_init['i_dict_weather_dataset_info'][
              dict_init['i_str_weather_dataset']]['str_base_path'] +=  '/'
              
        #modify init data to optimize performance

        if dict_init['ctrl_dict_cumulative_results'][
                'cumulation_level_time'] == "Hour" and \
                dict_init['i_dict_weather_dataset_info'][
                dict_init['i_str_weather_dataset']]['interval_minutes'] == 60:
            dict_init[
              'ctrl_dict_cumulative_results']['cumulation_level_time'] = "None"
        
        if isinstance(dict_init['ctrl_dict_cumulative_results'][
                'cumulation_level_space'], unicode) == True:
            dict_init[
              'ctrl_dict_cumulative_results']['cumulation_level_space'] = [
                dict_init['ctrl_dict_cumulative_results'][
                  'cumulation_level_space']]
            
        if isinstance(
                dict_init['ctrl_dict_individual_results'], unicode) == True:
            dict_init['ctrl_dict_individual_results'] = [
              dict_init['ctrl_dict_individual_results']]
        
        #create arr_timeinterval
        start = datetime.datetime.combine(
          dict_init['i_dict_dates']['arr_date_period'][0], 
          datetime.datetime.min.time()
        )
        end = datetime.datetime.combine(
          dict_init['i_dict_dates']['arr_date_period'][1] + \
          datetime.timedelta(days=1), 
          datetime.datetime.min.time()) - datetime.timedelta(
            seconds=dict_init['i_dict_weather_dataset_info'][dict_init[
              'i_str_weather_dataset']]['interval_minutes']*60)
        interval = datetime.timedelta(
          seconds=dict_init['i_dict_weather_dataset_info'][dict_init[
            'i_str_weather_dataset']]['interval_minutes']*60)
        arr_timestamp = [start + i * interval for i in range(
          int((end-start).total_seconds()/interval.total_seconds() + 1))]

        #establish connection to RLI Database server
        try:
            conn_rli_db = psycopg2.connect(
              database=dict_init['i_dict_db_connect']['database'], 
              host=dict_init['i_dict_db_connect']['host'], 
              user=dict_init['i_dict_db_connect']['user'], 
              password=dict_init['i_dict_db_connect']['password'])
            cur_rli_db = conn_rli_db.cursor()
            Info('Database connection established.', 2, dict_console_info)
        except:
            arr_error.append("Error! Connection with RLI database server " + \
              "could not be established: " + str(sys.exc_info()))
                
    else:
        arr_error.append('Error! No initialization variable as input argument given!')
        
    if arr_error != []:
        print arr_error[0]
        
    return arr_error, conn_rli_db, cur_rli_db, arr_timestamp, dict_init, str_boundary
    
    
    
    
