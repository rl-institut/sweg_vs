#!/usr/bin/python
# -*- coding: utf-8 -*-

def sweg_vs_save_result2db(dict_return, str_boundary, str_random_input, 
                           i_dict_result_output_database, conn_rli_db, 
                           cur_rli_db, ctrl_dict_individual_results, 
                           ctrl_dict_cumulative_results, dict_console_info,
                           i_dict_db_connect):
    '''   
    Saving sweg results to database.
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin
        
    Input:
    
        dict_return -- dictionary containing data to be saved to database
        
        str_boundary -- string containing name of geographic boundary
        
        str_random_input -- string containing path to random input
        
        i_dict_result_output_database -- dictionary containing info on target
                                         database
        
        conn_rli_db -- handle to psycopg connection
        
        cur_rli_db -- handle to psycopg cursor
        
        ctrl_dict_individual_results -- dictionary containing init info on
                                        detailed results
        
        ctrl_dict_cumulative_results -- dictionary containing init info on
                                        cumulative results
        
        dict_console_info -- dictionary containing information 
                             on the console logging functionality    
                             
        i_dict_db_connect -- dictionary containing information on db-connection
    ''' 
    #import additional modules
    import datetime
    import sys
    import psycopg2
    
    from Modules.sweg_vs_additional_modules import drop_column_in_db_table
    from Modules.sweg_vs_additional_modules import add_column_2_db_table
    from Modules.sweg_vs_additional_modules import update_row
    from Modules.sweg_vs_additional_modules import create_db_table
    from Modules.sweg_vs_additional_modules import insert_data_into_db_table
    from Modules.sweg_vs_additional_modules import retrieve_from_db_table
    from Modules.sweg_vs_additional_modules import insert_data_db_2
    from Modules.sweg_vs_additional_modules import delete_row
    from Modules.sweg_vs_additional_modules import add_comment2column
    from Modules.sweg_vs_additional_modules import retrieve_comment_from_column
    from Modules.sweg_vs_additional_modules import console_info as Info
    
    
    #declare variables
    arr_error = []
    arr_table_created = []
    schema = i_dict_result_output_database['str_schema']
    reference_timestamp = datetime.datetime.now().replace(microsecond=0)
    if dict_return['initialization']['ctrl_dict_cumulative_results'][
          'cumulation_level_time'] == "None":
        str_timestamp_dtype = "timestamp without time zone"
        str_cum_lvl = "o"
    elif dict_return['initialization']['ctrl_dict_cumulative_results'][
            'cumulation_level_time'] == "Hour":
        str_timestamp_dtype = "timestamp without time zone"
        str_cum_lvl = "1h"
    elif dict_return['initialization']['ctrl_dict_cumulative_results'][
            'cumulation_level_time'] == "Day":
        str_timestamp_dtype = "date"
        str_cum_lvl = "1d"
    elif dict_return['initialization']['ctrl_dict_cumulative_results'][
            'cumulation_level_time'] == "Period":
        str_timestamp_dtype = "character varying(50)"
        str_cum_lvl = "period"
    
    #define local functions
    
    def SaveData2DB(mode, result_type, str_timestamp_dtype, arr_table_created, 
                    schema, table_name, col_name, str_comment, cur_rli_db, 
                    conn_rli_db):
        
        if result_type == "cumulative_results" and \
                ctrl_dict_cumulative_results[
                'cumulation_level_time'] == "Period":
            #create table if not exists
            if isinstance(arr_insert_data[0], list) == True:
                create_db_table(
                  schema, table_name, 
                  ["id", "period", "spatial_lvl", "value", "sim_run_id"],[
                    "character varying(200)", str_timestamp_dtype, 
                     "character varying(100)", "numeric[]", "numeric"
                  ], "id", cur_rli_db, conn_rli_db
                )
            else:
                create_db_table(
                  schema, table_name, 
                  ["id", "period", "spatial_lvl", "value", "sim_run_id"], [
                    "character varying(200)", str_timestamp_dtype, 
                    "character varying(100)", "numeric", "numeric"
                  ], "id", cur_rli_db, conn_rli_db
                )
            str_id = col_name.replace('"', '')[col_name.index('_'):] + '_' + \
              str(int_checksum[0])
            #check if row already exists
            arr_retrieved = retrieve_from_db_table(
              schema, table_name, ["id"], cur_rli_db
            )
            if str_id not in arr_retrieved:
                #insert data
                insert_data_db_2(
                  schema, table_name, [
                    {'column_name': "id"},
                    {'column_name': "period"}, 
                    {'column_name': "spatial_lvl"}, 
                    {'column_name': "value"}, 
                    {'column_name': "sim_run_id"}
                  ], [
                  [str_id] + [dict_return['cumulative_results'][
                    'timestamp_python'][0]] + [
                      col_name.replace('"', '')[col_name.index('_'):]
                    ] + arr_insert_data + int_checksum
                  ], cur_rli_db, conn_rli_db
                )
            else:
                if mode == 'delete':
                    delete_row(schema, table_name, "sim_run_id", str_id, 
                               cur_rli_db, conn_rli_db
                    )
                    #insert data
                    insert_data_db_2(
                      schema, table_name, [
                        {'column_name': "id"},
                        {'column_name': "period"},
                        {'column_name': "spatial_lvl"},
                        {'column_name': "value"}, 
                        {'column_name': "sim_run_id"}
                      ], [
                      [str_id] + [dict_return['cumulative_results'][
                        'timestamp_python'][0]] + [
                          col_name.replace('"', '')[col_name.index('_'):]
                        ] + arr_insert_data + int_checksum
                      ], cur_rli_db, conn_rli_db
                    )
                    
                elif mode == 'update':
                    value_cond = arr_retrieved[arr_retrieved.index(str_id)]
                    update_row(schema, table_name, ["value"], 
                               [arr_insert_data], "id", 
                               [value_cond], cur_rli_db, conn_rli_db
                    )
        else:

            if table_name not in arr_table_created:
                #create table if not exists
                #print table_name
                create_db_table(schema, table_name, ["timestamp"],
                                [str_timestamp_dtype], "timestamp", cur_rli_db, 
                                conn_rli_db
                )
                #add name of created table to array in order to skip this creation of the same table for other values
                arr_table_created.append(table_name)
                #print arr_table_created
                #insert timestamp data if not exists
                if result_type == "cumulative_results":
                        insert_data_db_2(
                          schema, table_name, [{'column_name': "timestamp"}], [
                            [x] \
                            for x \
                            in dict_return['cumulative_results'][
                              'timestamp_python']
                          ], cur_rli_db, conn_rli_db
                        )
                else:
                    insert_data_db_2(schema, table_name, 
                                     [{'column_name': "timestamp"}], [
                                       [x] 
                                       for x 
                                       in dict_return['detailed_results'][
                                         'timestamp_python']
                                     ], cur_rli_db, conn_rli_db
                    )
       
                #invoke routine again to insert variable values
                arr_table_created = SaveData2DB(
                  mode, result_type, str_timestamp_dtype, arr_table_created, 
                  schema, table_name, col_name, str_comment, 
                  cur_rli_db, conn_rli_db
                )
            else:
                #check if column exists
                str_sql_statement = \
                  "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '" + \
                  table_name + "' and column_name = '" + \
                  col_name.replace('"',"") + "'"                    
                #print str_sql_statement
                cur_rli_db.execute(str_sql_statement)
                int_col_exists = cur_rli_db.fetchone()[0]
                #print table_name
                if int_col_exists != 0:
                    if mode == "drop":
                        #drop column
                        drop_column_in_db_table(schema, table_name, col_name, 
                                                cur_rli_db, conn_rli_db
                        )
                        #print 'column dropped.'
                        #create column
                        add_column_2_db_table(schema, table_name, col_name, 
                                              "numeric", cur_rli_db, 
                                              conn_rli_db)
                        Info('Column ' + table_name + '.' + col_name + \
                          " was recreated.", 3, dict_console_info)
                else:
                    add_column_2_db_table(schema, table_name, col_name, 
                                          "numeric", cur_rli_db, conn_rli_db
                    )
                    
                if result_type == "cumulative_results":
                    update_row(schema, table_name, [col_name], 
                               [list(arr_insert_data)], "timestamp", 
                                dict_return['cumulative_results'][
                                  'timestamp_python'], cur_rli_db, conn_rli_db
                    )
                else:
                    update_row(schema, table_name, [col_name], 
                               [list(arr_insert_data)], "timestamp", 
                                dict_return['detailed_results'][
                                  'timestamp_python'], cur_rli_db, conn_rli_db
                    )
                   
                #check for existing comment on column and add new column to it
                str_comment_retrieved = retrieve_comment_from_column(
                  schema, table_name, col_name, cur_rli_db, conn_rli_db
                )
                if str_comment != str_comment_retrieved and \
                        str_comment_retrieved != []:
                    add_comment2column(schema, table_name, col_name, 
                                       str_comment_retrieved[0] + "\n" +
                                       str_comment, cur_rli_db, conn_rli_db
                    )
                else:
                    add_comment2column(schema, table_name, col_name, 
                                       str_comment, cur_rli_db, conn_rli_db
                    )
        
        return arr_table_created
    
    
    #insert info into result_info table
    arr_dict_columns_info = [
      {'column_name': "id", 'column_type': "numeric",}, 
      {'column_name': "creation_timestamp", 
      'column_type': 'timestamp without time zone'}, 
      {'column_name': "boundary", 'column_type': 'character varying(60)'},
      {'column_name': "installation_register", 
      'column_type': 'character varying(60)'},
      {'column_name': "weather_data", 'column_type': 'character varying(20)'}, 
      {'column_name': "period_start", 'column_type': 'date'},
      {'column_name': "period_end", 'column_type': 'date '},
      {'column_name': "windspeed_correction", 
      'column_type': 'character varying(20)'},
      {'column_name': "v_dependency_factor", 'column_type': 'numeric'}, 
      {'column_name': "ideal_square_simple_factor", 'column_type': 'numeric'},
      {'column_name': "non_availabilities_misc", 
      'column_type': 'character varying(20)'},
      {'column_name': "wind_index", 
      'column_type': 'character varying(30)'},
      {'column_name': "reference_flh", 
      'column_type': 'character varying(20)'},
      {'column_name': "flh_mean_range", 
      'column_type': 'character varying(20)'},
      {'column_name': "random_input_saved", 'column_type': 'integer'},
      {'column_name': "random_input_load", 'column_type': 'integer'},
      {'column_name': "random_input_path", 
      'column_type': 'character varying(600)'},
      {'column_name': "individual_results", 
      'column_type': 'character varying(25)[]'},
      {'column_name': "cumulative_results_space", 
      'column_type': 'character varying(25)[]'},
      {'column_name': "cumulative_results_time", 
      'column_type': 'character varying(10)'},
      {'column_name': "cumulative_results_timeseries_format", 
      'column_type': 'character varying(15)'},
      {'column_name': "multiprocessing_enabled", 'column_type': 'integer'},
      {'column_name': "nr_of_processors", 'column_type': 'integer'},
      {'column_name': "simulation_runtime_sec", 'column_type': 'numeric'}
    ]
    
    #check connection and if necessary reestablish database connection
    
    if conn_rli_db.closed == 0:
        try:
            conn_rli_db = psycopg2.connect(
              database=i_dict_db_connect['database'], 
              host=i_dict_db_connect['host'], 
              user=i_dict_db_connect['user'], 
              password=i_dict_db_connect['password'])
            cur_rli_db = conn_rli_db.cursor()
            Info('Database connection established.', 2, dict_console_info)
        except:
            arr_error.append("Error! Connection with RLI database server " + \
              "could not be established: " + str(sys.exc_info()))
                             
    #create table if not exists
    create_db_table(schema, 
                    i_dict_result_output_database['str_table_result_info'], [
                      x['column_name'] 
                      for x 
                      in arr_dict_columns_info
                    ], [
                      x['column_type'] 
                      for x 
                      in arr_dict_columns_info
                    ], "id", cur_rli_db, conn_rli_db
    )
            
    if 'full_load_hours' in dict_return[
            'initialization']['i_result_postprocessing']['method']:
        str_wind_index = str(
          dict_return['initialization']['i_result_postprocessing'][
            'flh_setup']['wind_index']
        )
        str_ref_flh = str(dict_return['initialization'][
          'i_result_postprocessing']['flh_setup'][
            'flh_min_mean_max'][0]) + ', ' + str(dict_return['initialization'][
          'i_result_postprocessing']['flh_setup'][
            'flh_min_mean_max'][1]) + ', ' + str(dict_return['initialization'][
          'i_result_postprocessing']['flh_setup'][
            'flh_min_mean_max'][2])
        str_flh_range = str(dict_return['initialization'][
          'i_result_postprocessing']['flh_setup'][
            'flh_mean_range'][0]) + ', ' + str(dict_return['initialization'][
          'i_result_postprocessing']['flh_setup'][
            'flh_mean_range'][1])
    else:
        str_wind_index = '-'
        str_ref_flh = '-'
        str_flh_range = '-'
    arr_insert_data_1 = [
      reference_timestamp, 
      str_boundary, 
      dict_return['initialization']['i_dict_register_info']['str_schema'] + \
      "." + dict_return['initialization']['i_dict_register_info']['str_data'], 
      dict_return['initialization']['i_str_weather_dataset'], 
      dict_return['initialization']['i_dict_dates']['arr_date_period'][0], 
      dict_return['initialization']['i_dict_dates']['arr_date_period'][1],
      dict_return['initialization']['i_dict_windspeed_corr']['height_corr'],
      dict_return['initialization']['i_dict_windfarm_efficiencies'][
        'v_dependency']['factor'],
      dict_return['initialization']['i_dict_windfarm_efficiencies'][
        'ideal_square_simple']['factor'], str(
          dict_return['initialization']['i_dict_non_availabilities'][
            'misc']['Frequency']) + ',' + str(dict_return['initialization'][
              'i_dict_non_availabilities']['misc']['Rate']
        ) + ',' + str(
          dict_return['initialization']['i_dict_non_availabilities'][
            'misc']['DowntimeHours']
        ), 
      str_wind_index,
      str_ref_flh,
      str_flh_range,
      dict_return['initialization']['i_dict_random_input']['bol_save'],
      dict_return['initialization']['i_dict_random_input']['bol_load'],
      str_random_input,
      [x.rstrip() for x in dict_return['initialization'][
        'ctrl_dict_individual_results']
      ],
      dict_return['initialization']['ctrl_dict_cumulative_results'][
        'cumulation_level_space'],
      dict_return['initialization']['ctrl_dict_cumulative_results'][
        'cumulation_level_time'],
      dict_return['initialization']['ctrl_dict_cumulative_results'][
        'timeseries_format'],
      dict_return['initialization']['ctrl_bol_multiprocessing']['enabled'],
      dict_return['initialization']['ctrl_bol_multiprocessing'][
        'nr_of_processors'],
      (datetime.datetime.now() - \
      dict_console_info['time_start']).total_seconds()
    ]
                       
                       
    #calculate checksum of arr_insert_data[1:-1] without sublists, source: http://stackoverflow.com/questions/6923780/python-checksum-of-a-dict
    int_checksum = [
      abs(reduce(
        lambda x,y : x^y, [hash(x) 
        for x 
        in arr_insert_data_1[1:-1] 
        if isinstance(x, list) != True])
      )
    ]
    arr_insert_data = [int_checksum +  arr_insert_data_1]
    #print arr_insert_data
    try:
        arr_retrieved = retrieve_from_db_table(
          schema, i_dict_result_output_database['str_table_result_info'], 
          ["id"], cur_rli_db
        )
        if int_checksum[0] not in arr_retrieved:
            insert_data_into_db_table(
              schema, i_dict_result_output_database['str_table_result_info'], 
              arr_dict_columns_info, arr_insert_data, cur_rli_db, conn_rli_db
            )
            Info("Simulation details saved to database under ID: " + \
              str(int_checksum[0]),1, dict_console_info
            )
        else:
            value_cond = arr_retrieved[arr_retrieved.index(int_checksum[0])]
            update_row(schema, 
              i_dict_result_output_database['str_table_result_info'], 
              ["creation_timestamp", "simulation_runtime_sec"], 
              [[arr_insert_data[0][1]], [arr_insert_data[0][-1]]], 
              arr_dict_columns_info[0]['column_name'], 
              [value_cond], cur_rli_db, conn_rli_db
            )
            Info("Simulation details of repeated run are updated in database: " + \
              str(int_checksum[0]),1, dict_console_info
            )
    except Exception,e:
        print e.pgerror
        arr_error.append("Error: " + str(sys.exc_info()))    
        
    
    
    #iterate over all data of interest
    
    for results in ["cumulative_results", "detailed_results"]:
        if results == "cumulative_results" and \
                dict_return['cumulative_results'] != {}:
            Info('Cumulative results are being saved to database...', \
              1, dict_console_info
            )
            for cumulation_level_space in [
                    x for x in dict_return[results].iterkeys() 
                    if x != 'timestamp_matlab' and \
                    x != 'timestamp_python' and \
                    x != 'desc' and x != 'comments']:
                Info('Saving results of level ' + \
                  str(cumulation_level_space), 3, dict_console_info
                )
                if cumulation_level_space == 'boundary':
                    for str_variable, values in \
                            dict_return[results][
                              cumulation_level_space].iteritems():
                                  
                        if str_variable in i_dict_result_output_database[
                                'output_variables']:

                            table_name = "cum" + "_" + str_cum_lvl + "_" +  \
                              dict_return['initialization'][
                                'i_dict_register_info']['register_name'] + \
                              "_" + dict_return['initialization'][
                                'i_str_weather_dataset'].replace('-', '_') + \
                              "_" + str_variable + "_" + \
                              dict_return['initialization'][
                                'ctrl_dict_cumulative_results'][
                                  'timeseries_format']
                            col_name = '"' + cumulation_level_space + '"'
                            str_comment = \
                              "Cumulative simulation results of SWEG_VS module. See table " + \
                              schema + "." + i_dict_result_output_database[
                                'str_table_result_info'] + ", id: " + \
                              str(int_checksum[0]) + \
                              ", for additional information on simulation parameters."
                            arr_insert_data = values
                        
                            arr_table_created = SaveData2DB(
                              i_dict_result_output_database['existing_data'], 
                              results, str_timestamp_dtype, arr_table_created, 
                              schema, table_name.lower(), col_name.lower(), 
                              str_comment, cur_rli_db, conn_rli_db
                            )

                else:
                    for adm_lvl in \
                            dict_return[results][cumulation_level_space].iterkeys():
                        for str_variable, values in \
                                dict_return[results][
                                  cumulation_level_space][adm_lvl].iteritems():
                            if str_variable in i_dict_result_output_database[
                                    'output_variables']:
                                table_name = "cum" + "_" + str_cum_lvl + "_" +\
                                  dict_return['initialization'][
                                    'i_dict_register_info']['register_name'] +\
                                    "_" + dict_return['initialization'][
                                      'i_str_weather_dataset'].replace('-', '_') + \
                                    "_" + str_variable + "_" + \
                                    dict_return['initialization'][
                                      'ctrl_dict_cumulative_results'][
                                        'timeseries_format']
                                adm_lvl = adm_lvl.rstrip('_')
                                if '_' in adm_lvl and ' ' in adm_lvl:
                                    #compose column_name: cumulation_level_space + rli_wp_id + wec_producer
                                    col_name = '"' + cumulation_level_space + \
                                      "_" + adm_lvl[
                                        :adm_lvl.index(' ', len(adm_lvl) - \
                                        adm_lvl[::-1].find('_'))
                                      ] + '"'
                                else:
                                    col_name = '"' + cumulation_level_space + \
                                      "_" + adm_lvl + '"'
                                str_comment = \
                                  "Cumulative simulation results of SWEG_VS module. See table " + \
                                  schema + "." + i_dict_result_output_database[
                                    'str_table_result_info'] + ", id: " + \
                                    str(int_checksum[0]) + \
                                    ", for additional information on simulation parameters."
                                arr_insert_data = values
                                #print table_name, col_name
                                arr_table_created = SaveData2DB(
                                  i_dict_result_output_database['existing_data'], 
                                  results, str_timestamp_dtype, arr_table_created, 
                                  schema, table_name.lower(), col_name.lower(), 
                                 str_comment, cur_rli_db, conn_rli_db
                                )
                            
            Info('Cumulative results successfully saved to database.', 
              1, dict_console_info
            )
                        
                        
        elif results == "detailed_results" and \
                dict_return['detailed_results'] != {}:
            Info('Detailed results are being saved to database...', 
              1, dict_console_info)
            for gridcell in [x for x in dict_return[results].iterkeys() \
                    if x != 'timestamp_matlab' and x != 'timestamp_python']:
                Info('Saving results of gridcell ' + str(gridcell), 
                  3, dict_console_info)
                for wp in dict_return[results][gridcell][
                        'generation'].iterkeys():
                    for str_variable, values in {
                            key: value 
                            for key,value 
                            in dict_return[results][gridcell][
                              'generation'][wp].iteritems() 
                            if key != 'anlagen_nabenhoehe' and \
                              key != 'anlagen_rotordm' and \
                              key != 'operation_hours' and \
                              key in ctrl_dict_individual_results}.iteritems():

                        table_name = dict_return['initialization'][
                          'i_dict_register_info']['register_name'] + \
                          "_" + dict_return['initialization'][
                            'i_str_weather_dataset'].replace('-', '_') + \
                          "_" + str_variable
                        col_name = '"' + wp + '"'
                        str_comment = \
                          "Detailed simulation results of SWEG_VS module. See table " + \
                          schema + "." + i_dict_result_output_database[
                            'str_table_result_info'] + ", id: " + \
                          str(int_checksum[0]) + \
                          ", for additional information on simulation parameters."
                        arr_insert_data = [float(x) for x in values]
                        
                        arr_table_created = SaveData2DB(
                          i_dict_result_output_database['existing_data'], 
                          results, "timestamp without time zone", 
                          arr_table_created, schema, table_name.lower(), 
                          col_name.lower(), str_comment, cur_rli_db, conn_rli_db
                        )
            
            Info('Detailed results successfully saved to database.', 
              1, dict_console_info
            )
        
    return arr_error