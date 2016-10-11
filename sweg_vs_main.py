#!/usr/bin/python
# -*- coding: utf-8 -*-

def sweg_vs_main(init, dict_char_replace=None):
    '''Simulates wind energy based electricity generation.
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin
    
    Keyword arguments:

    init -- path to .mat file with initialization details OR
        variable containing dictionary with initialization details   
        
    dict_char_replace -- dictionary with pairs of symbols/Umlaute 
        and their replacement, necessary to restore possibly existing forbidden 
        symbols in initialization variable
               
    IMPORTANT:
        
        Add path to SWEG_VS folder to Environment variable PYTHONPATH
    
        Install additional necessary modules if you want to use .shp-files:
        
            - pyshp (http://code.google.com/p/pyshp/)
            - ppygis (http://www.fabianowski.eu/projects/ppygis/index.html)
    '''
    
    #import additional modules
    import datetime 
    import math
    import scipy.io as spio
    import sys
    import getpass
    from multiprocessing import Process, Queue
    
    from Modules.sweg_vs_initialization import sweg_vs_initialization as Ini
    from Modules.sweg_vs_retrieve_db_data import \
      sweg_vs_retrieve_db_data as RetDB
    from Modules.sweg_vs_additional_modules import console_info as Info
    from Modules.sweg_vs_retrieve_weatherdata import \
      sweg_vs_retrieve_weatherdata as RetWeat
    from Modules.sweg_vs_calculate_electricity_generation import \
      sweg_vs_calculate_electricity_generation as CalcGen
    from Modules.sweg_vs_calculate_cumulative_results import \
      sweg_vs_calculate_cumulative_results as CalcCum
    from Modules.sweg_vs_save_result2db import \
      sweg_vs_save_result2db as SaveResult2DB

    #define local function                    
                        
    def calculate_generation(arr_gridcell_id, int_processor, 
                            dict_random_input, out_q):
        '''
        Calculates the electricity generation from windturbines in 
        the current gridcell.
        '''
        dict_result = {}
        int_grid_counter = 1
        
        for grid_cell in arr_gridcell_id:
            #select wind farms from register within current gridcell
            arr_register_cell = \
              [row for row in arr_register if row[15] == grid_cell[0]]
            #get minimum and maximum hubheight
            hubheights = \
              [float(windfarm[8]) for windfarm in list(arr_register_cell)]
            hubheight_limits = [min(hubheights), max(hubheights)]
            #get roughness lengths
            if i_dict_windspeed_corr['height_corr'] != 'linear':
                z0 = float(arr_z0[1][arr_z0[0].index(grid_cell[0])])
            else:
                z0 = None
            #retrieve weather data for the specified region and time
            arr_error_retweat, arr_windspeed, \
            arr_density, arr_winddirection, arr_heights = \
              RetWeat(grid_cell, i_str_weather_dataset, 
                      i_dict_weather_dataset_info, hubheight_limits, 
                      i_dict_dates, dict_console_info)
                                 
            if arr_error_retweat == []:
                #calculate electricity generation
                Info("Kernel " + str(int_processor) + \
                     ": Weather Data Gridcell " + str(grid_cell[0]) + ": " + 
                     str(int_grid_counter) + "/" + str(len(arr_gridcell_id)),
                     1, dict_console_info)
                arr_error_calcgen, dict_generation = CalcGen(
                    grid_cell[0], i_str_weather_dataset, 
                    i_dict_weather_dataset_info, i_dict_dates, 
                    i_int_max_runtime_wec, arr_timestamp, arr_register_cell, 
                    arr_cp, arr_P, arr_P_shares, z0, arr_windspeed, 
                    arr_winddirection, arr_heights, i_dict_windspeed_corr,
                    i_dict_windfarm_efficiencies, i_dict_non_availabilities, arr_density, 
                    dict_random_input, dict_console_info, ctrl_dict_charts, 
                    ctrl_dict_individual_results, int_processor, 
                    i_dict_powercurve_mix, i_result_postprocessing)
                
                if arr_error_calcgen == []:
                    #assigning results to dict_result
                    dict_result[str(grid_cell[0])] = {}
                    dict_result[str(grid_cell[0])]['x'] = str(grid_cell[1])
                    dict_result[str(grid_cell[0])]['y'] = str(grid_cell[2])
                    dict_result[str(grid_cell[0])]['generation'] = \
                      dict_generation
                    #print dict_result 
            
            int_grid_counter += 1
            
        if ctrl_bol_multiprocessing['enabled'] == 0:
            return dict_result
        elif ctrl_bol_multiprocessing['enabled'] == 1:
            out_q.put(dict_result)

  
    #declare variables
    dict_result = {}
    dict_detailed_results = {}
    dict_return = {}
    
    #begin of main code section
    
    #get current time to calculate runtime        
    time_start = datetime.datetime.now()
    
    print '+++++++++++++++++++++++++++++++++++++++++++++++++++' + \
     '++++++++++++++++++++++++++++++'
    print '                                 RLI Windtool 2.0                '+\
      '            '
    print '            (c) 2013, Marcus Biank, Reiner Lemoine Institut, Berlin\
                '
    print '+++++++++++++++++++++++++++++++++++++++++++++++++++' + \
      '++++++++++++++++++++++++++++++'
    print ''
    print 'Simulation run by ' + getpass.getuser()  + ' on ' + \
          str(time_start.replace(microsecond=0))
    print ''
    print 'Info_____________________________________________________________'+\
      '_______Time_in_s'
    print ''
        
    try:    
        print '{0:74}{1:4.5f}'.format("Start",(datetime.datetime.now() - \
              time_start).total_seconds())
        
        #Run initialization script
        arr_error_ini, conn_rli_db, cur_rli_db, arr_timestamp, \
        dict_init, str_boundary = Ini(init, dict_char_replace, time_start)
        
        if arr_error_ini == []:
        
            #assing contents of dict_init to specific SWEG_VS variables
            i_dict_db_connect = dict_init['i_dict_db_connect']
            i_dict_boundary = dict_init['i_dict_boundary']
            i_dict_register_info = dict_init['i_dict_register_info']
            i_int_max_runtime_wec = dict_init['i_int_max_runtime_wec']
            i_dict_performance_curves_info = \
              dict_init['i_dict_performance_curves_info']
            i_dict_powercurve_mix = dict_init['i_dict_powercurve_mix']
            i_str_weather_dataset = dict_init['i_str_weather_dataset']
            i_dict_weather_dataset_info = \
              dict_init['i_dict_weather_dataset_info']
            i_dict_weather_grid_info = dict_init['i_dict_weather_grid_info']
            i_dict_dates = dict_init['i_dict_dates']
            i_dict_z0_info = dict_init['i_dict_z0_info']
            i_dict_random_input = dict_init['i_dict_random_input']
            i_dict_windspeed_corr = dict_init['i_dict_windspeed_corr']
            i_dict_windfarm_efficiencies = \
              dict_init['i_dict_windfarm_efficiencies']
            i_dict_non_availabilities = \
              dict_init['i_dict_non_availabilities']
            i_result_postprocessing = dict_init['i_result_postprocessing']
            i_dict_result_output_variable = \
              dict_init['i_dict_result_output_variable']
            i_dict_result_output_database = \
              dict_init['i_dict_result_output_database']
            i_dict_result_output_mat = dict_init['i_dict_result_output_mat']
            ctrl_dict_charts = dict_init['ctrl_dict_charts']
            ctrl_dict_individual_results = \
              [x.rstrip() for x in dict_init['ctrl_dict_individual_results']]
            ctrl_dict_cumulative_results = \
              dict_init['ctrl_dict_cumulative_results']
            ctrl_dict_logging = dict_init['ctrl_dict_logging']
            ctrl_dict_console_output = dict_init['ctrl_dict_console_output']
            ctrl_bol_multiprocessing = dict_init['ctrl_bol_multiprocessing']
            
            #defining dict_console_info = 
            #basic variable for SWEG_VS_Console_Info, the reporting module
            dict_console_info = \
              {'time_start': time_start, 'ctrl_bol_console_output': \
              ctrl_dict_console_output['bol_console_output'],
              'ctrl_int_console_details': \
              ctrl_dict_console_output['int_console_details']}
        
            Info("Initialization successfully completed.",1, dict_console_info) 
            
            #retrieve data from the local database
            arr_error_retdb, arr_register, arr_administration, \
            arr_gridcell_id, arr_cp, arr_P, arr_P_shares, arr_z0, \
            dict_random_input = RetDB(
                cur_rli_db, i_dict_boundary, i_dict_register_info, 
                i_str_weather_dataset, i_dict_weather_grid_info, 
                i_dict_performance_curves_info, i_dict_powercurve_mix,
                i_dict_windspeed_corr, i_dict_z0_info, i_dict_random_input, 
                dict_console_info)
            
            if arr_error_retdb == []:
                
                #print arr_gridcell_id[0]
                
                Info("Calculation of electricity generation.", 1, 
                     dict_console_info)
                     
                #add timestamps to result variable
                dict_result['timestamp_python'] = arr_timestamp
                dict_result['timestamp_matlab'] = [
                    d.strftime("%d-%b-%Y %H:%M:%S") 
                    for d in dict_result['timestamp_python']]
                
                if ctrl_bol_multiprocessing['enabled'] == 0:
                    #procedure without threading
                    Info("Multiprocessing disabled.", 3, dict_console_info)
                
                    dict_result.update(calculate_generation(arr_gridcell_id, 1, 
                                                      dict_random_input, ""))
                    
                elif ctrl_bol_multiprocessing['enabled'] == 1:
                    #procedure with threading
                    Info("Multiprocessing enabled.", 3, dict_console_info)
                    
                    """
                    source: http://eli.thegreenplace.net/2012/01/16/python-
                    parallelizing-cpu-bound-tasks-with-multiprocessing/
                    """
                    try:
                        #define queue used by all processes for result output
                        out_q = Queue(50)
                        #calculate arguments per processor
                        chunksize = \
                          int(math.ceil(
                          len(arr_gridcell_id) / 
                          float(ctrl_bol_multiprocessing['nr_of_processors'])))
                        #print chunksize
                        procs = []
                        
                        #assign function and arguments to individual 
                        #processors and then start processes
                        for i in range(
                          ctrl_bol_multiprocessing['nr_of_processors']):
                            proc_p = Process(
                              target=calculate_generation,
                              args=(arr_gridcell_id[
                                chunksize * i:chunksize * (i + 1)],
                                i + 1, dict_random_input, out_q))
                            procs.append(proc_p)
                            proc_p.start()
                        
                        # Collect all results into a single result dict. 
                        for i in range(
                          ctrl_bol_multiprocessing['nr_of_processors']):
                            dict_result.update(out_q.get())
                    
                        # Wait for all worker processes to finish
                        for proc in procs:
                            proc.join()
                        Info('Multiprocessing of calculation finished.', 
                             1, dict_console_info)
                    except Exception:
                        print "Error: " + str(sys.exc_info())
                                          
                #save dict with random input data 
                if i_dict_random_input['bol_save'] == True and \
                   dict_random_input == {}:
                    #extract availability info from dict_result
                    
                    dict_random_input = dict(
                         (k,v) \
                         for d 
                         in [
                           {wp: {
                               key:value \
                               for (key,value) 
                               in dict_result[
                                 gridcell]['generation'][wp].iteritems() 
                               if key == 'availability'
                             } 
                             for wp 
                             in dict_result[gridcell]['generation'].iterkeys()
                          } 
                          for gridcell 
                          in dict_result.iterkeys() 
                          if gridcell != 'timestamp_python' and \
                            gridcell != 'timestamp_matlab'
                        ] 
                        for (k,v) 
                        in d.items()
                    )

                    #print dict_random_input
                    #save availability info 
                    #sweg_vs_random_input_register_boundary_timeperiod.mat
                        
                    str_random_input = \
                      "sweg_vs_random_input_" + \
                      i_dict_register_info['str_schema'] + "_" + \
                      i_dict_register_info['str_data']  + "_" + str_boundary +\
                      "_" + str(i_dict_dates['arr_date_period'][0]) + \
                      "_" + str(i_dict_dates['arr_date_period'][1]) + "_" +\
                      str(datetime.date.today()) + ".mat"
                    
                    try:
                        spio.savemat(i_dict_random_input['str_save_path'] + \
                                     str_random_input, 
                                     dict_random_input, oned_as = 'row')
                        Info('Timeseries of random input was saved.',
                             1, dict_console_info)
                    except Exception:
                        print 'An error occured: ' + str(sys.exc_info()) 
                else:
                    str_random_input = i_dict_random_input['str_load_path']
                
                Info('''Electricity generation for boundary successfully calculated.''', 
                     1, dict_console_info)
                
                       
                #calculate cumulative results
                arr_error_calccum, dict_cum_result = \
                  CalcCum(dict_result, ctrl_dict_cumulative_results, 
                          arr_register,i_str_weather_dataset,
                          i_dict_weather_dataset_info, arr_administration, 
                          i_result_postprocessing, dict_console_info)
                
                #only return detailed results 
                #if variables are specified in init variable
                if ctrl_dict_individual_results != []:
                    dict_detailed_results = dict_result
                    
                #compose dict_return
                dict_return['initialization'] = dict_init
                dict_return['cumulative_results'] = dict_cum_result
                dict_return['detailed_results'] = dict_detailed_results
                
                #write dict_return to .mat file
                
                if i_dict_result_output_mat['bol_mat_output'] == True:
                    str_output_mat = \
                      "sweg_vs_output_" + \
                      i_dict_register_info['str_schema'] + "_" + \
                      i_dict_register_info['str_data']  + "_" + str_boundary +\
                      str(i_dict_dates['arr_date_period'][0]) + \
                      "_" + str(i_dict_dates['arr_date_period'][1]) + "_" +\
                      str(datetime.date.today()) + ".mat"
                    
                    try:
                        spio.savemat(
                            i_dict_result_output_mat['str_mat_output_path'] + \
                            str_output_mat, dict_return, oned_as = 'row')
                        Info('Result variable was saved as mat file.',
                             1, dict_console_info)
                    except Exception:
                        print 'An error occured: ' + str(sys.exc_info()) 
                        Info('Result variable was not saved as mat file.',
                             1, dict_console_info)
                        pass
                            
                #database output
                if i_dict_result_output_database['bol_database_output'] == True:
                    arr_error_saveresults2db = \
                      SaveResult2DB(dict_return, str_boundary.replace("_", ""),
                                    i_dict_random_input['str_save_path'] + \
                                    str_random_input, 
                                    i_dict_result_output_database, 
                                    conn_rli_db, cur_rli_db, 
                                    ctrl_dict_individual_results, 
                                    ctrl_dict_cumulative_results,
                                    dict_console_info, i_dict_db_connect)
                    if arr_error_saveresults2db != []:
                        print arr_error_saveresults2db
                    
                '''
                mat file output is not properly working for mat format <7.2, 
                hdf with better functionality requires h5py and the building 
                of the hdf file from the dict_return
                if i_dict_result_output_mat['bol_mat_output'] == True:
                    str_mat_filename = \
                      i_dict_result_output_mat['str_mat_output_path'] + \
                      "sweg_vs_output_" + \
                      i_dict_register_info['str_schema'] + "_" + \
                      i_dict_register_info['str_data'] + "_" + \
                      str(i_dict_dates['arr_date_period'][0]) + "_" + \
                      str(i_dict_dates['arr_date_period'][1]) + ".mat"
                    try:
                        print str_mat_filename
                        spio.savemat(str_mat_filename, dict_return, 
                          oned_as='row')
                        
                        print 'Initialization file SWEG_VS_init.mat was created!'
                    except:
                        print 'An error occured: ' + str(sys.exc_info()) 
                '''
                print ''
                print "Calculations successfully finished. Congratulations!"
                print ''
                print '+++++++++++++++++++++++++++++++++++++++++++++++++++' + \
                  '++++++++++++++++++++++++++++++'
                print '                                     THE END       ' + \
                  '                       '
                print '              (c) 2013, Marcus Biank,' + \
                  'Reiner Lemoine Institut, Berlin              '
                print '+++++++++++++++++++++++++++++++++++++++++++++++++++' + \
                  '++++++++++++++++++++++++++++++'
        
        #close connection to RLI Database server
        cur_rli_db.close()
        conn_rli_db.close()
        
        #output of results
        if i_dict_result_output_variable == True:
            return dict_return
    
    except Exception:
        print "Error: " + str(sys.exc_info())
        return "Error: " + str(sys.exc_info())
        
        
