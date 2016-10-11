#!/usr/bin/python
# -*- coding: utf-8 -*-

def sweg_vs_retrieve_db_data(cur_rli_db, i_dict_boundary, i_dict_register_info, 
  i_str_weather_dataset, i_dict_weather_grid_info, 
  i_dict_performance_curves_info, i_dict_powercurve_mix, 
  i_dict_windspeed_corr, i_dict_z0_info, i_dict_random_input, 
  dict_console_info):
    '''
    Retrieves simulation input data from a local database.
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin
    
    Keyword arguments:        
    
        cur_rli_db -- cursor on database connection
        
        i_dict_boundary -- dictionary containing information on 
                           a existing boundary conditions 
        
        i_dict_register_info -- dictionary containing information on the wind 
                                installation register to be used
        
        i_str_weather_dataset -- string specifying which dataset is to be used
        
        i_dict_weather_grid_info -- dictionary containing information 
                                    on the weather datasets
        
        i_dict_performance_curves_info -- dictionary containing information on 
                                          the performance curves to be used
                                          
        i_dict_powercurve_mix -- dictionary containing information on source
                                 for power curve mixing
        
        i_dict_windspeed_corr -- dict specifying which method for windspeed 
                                 correction is to be used
        
        i_dict_windfarm_efficiencies -- dict specifying how wind farm 
                                        efficiencies are to be calculated
        
        i_dict_z0_info -- dictionary containing information on z0
        
        i_dict_random_input -- dictionary containing information on the usage 
                               of randomly generated data
        
        dict_console_info -- dictionary containing information on the console 
                             logging functionality
    ''' 
    
    #import additional modules 
    import shapefile
    import sys
    import ppygis
    
    from Modules.sweg_vs_additional_modules import console_info as Info
    from Modules.sweg_vs_additional_modules import loadmat
    
    #declare local variables 
    arr_error = []
    arr_register = []
    arr_administration = []
    arr_gridcell_id = []
    arr_shp_points = []
    arr_cp = []
    arr_P = []
    arr_P_shares = []
    arr_z0 = []
    dict_random_input = {}
    
    #detect source for boundary polygon
    if i_dict_boundary['source'] == "GeoDB":
        #compose sql statement for additional boundary query
        str_sql_statement_bound_src = ", " + \
          i_dict_boundary['dict_boundary_geodb']['str_schema'] + "." + \
          i_dict_boundary['dict_boundary_geodb']['str_data'] + " AS boundary "
        if i_dict_boundary['dict_boundary_geodb']['str_geom_adminlvl'] == "Land":
            str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_column'] + \
              ", register.geom) AND boundary.bez_nat = '" + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_name'] + \
              '''' AND boundary.bez_lan is NULL AND 
                   boundary.bez_rbz is NULL AND 
                   boundary.bez_krs is NULL AND 
                   boundary.bez_vwg is NULL AND 
                   boundary.bez_gem is NULL '''
        elif i_dict_boundary['dict_boundary_geodb']['str_geom_adminlvl'] == "Bundesland":
            str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_column'] + \
              ", register.geom) AND boundary.bez_lan = '" + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_name'] + \
              '''' AND boundary.bez_rbz is NULL AND 
                   boundary.bez_krs is NULL AND 
                   boundary.bez_vwg is NULL AND 
                   boundary.bez_gem is NULL '''
        elif i_dict_boundary['dict_boundary_geodb'][
                'str_geom_adminlvl'] == "Regierungsbezirk":
            str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_column'] + \
              ", register.geom) AND boundary.bez_rbz = '" + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_name'] + \
              '''' AND boundary.bez_krs is NULL AND 
                   boundary.bez_vwg is NULL AND 
                   boundary.bez_gem is NULL '''
        elif i_dict_boundary['dict_boundary_geodb']['str_geom_adminlvl'] == "Kreis":
            str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_column'] + \
              ", register.geom) AND boundary.bez_krs = '" + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_name'] + \
              '''' AND boundary.bez_vwg is NULL AND 
                   boundary.bez_gem is NULL '''
        elif i_dict_boundary['dict_boundary_geodb'][
                'str_geom_adminlvl'] == "Verwaltungsgemeinschaft":
            str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_column'] + \
              ", register.geom) AND boundary.bez_vwg = '" + \
              i_dict_boundary['dict_boundary_geodb']['str_geom_name'] + \
              "' AND boundary.bez_gem is NULL "
        elif i_dict_boundary['dict_boundary_geodb']['str_geom_adminlvl'] == "Gemeinde":
            str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
            i_dict_boundary['dict_boundary_geodb']['str_geom_column'] + \
            ", register.geom) AND boundary.bez_gem = '" + \
            i_dict_boundary['dict_boundary_geodb']['str_geom_name'] + "' "
            
    elif i_dict_boundary['source'] == "Shapefile":
        #compose sql statement for additional boundary query
        #set database relevant variables to ""
        str_sql_statement_bound_src = ""
        try:
            shp_file = shapefile.Reader(
              str(i_dict_boundary['str_shp_filepath']))
            Info("Shapefile successfully read.", 2, dict_console_info)
            shp_shapes = shp_file.shapes()
            Info("Number of shapes in shp_file: " +  \
              str(len(shp_shapes)), 2,dict_console_info)
            
            if len(shp_shapes) == 1:
                #define points
                for point in shp_shapes[0].points:
                    arr_shp_points.append(
                      ppygis.Point(point[0],point[1], 4326))
                arr_shp_points.append(
                  ppygis.Point(shp_shapes[0].points[0][0],
                               shp_shapes[0].points[0][1], 4326))
                #define linestring ring
                postgis_shp_linestring =[ppygis.LineString(
                  arr_shp_points, 4326)]
                #define polygon
                postgis_shp_polygon = ppygis.Polygon(
                  postgis_shp_linestring, 4326)
                #define ewkb (extended well-known binary) of polygon
                str_shpgeom = ppygis.Geometry.getquoted(
                  postgis_shp_polygon)
                
                str_sql_statement_bound_cond = "AND ST_CONTAINS(" + \
                  str_shpgeom + ", register.geom) "
                #print str_sql_statement_bound_cond
            else:
                arr_error.append("Error: " + str(len(shp_shapes)) + \
                  " shapes in the provided shapefile! Only one allowed.")
        except:
            arr_error.append("Error: " + str(sys.exc_info()))
        
    elif i_dict_boundary['source'] == "DBtable":
        #compose sql statement for additional boundary query
        str_sql_statement_bound_src = ", " + \
          i_dict_boundary['dict_boundary_dbtable']['str_schema'] + "." + \
          i_dict_boundary['dict_boundary_dbtable']['str_data'] + " AS boundary "
          
        str_sql_statement_bound_cond = "AND ST_CONTAINS(boundary." + \
              i_dict_boundary['dict_boundary_dbtable']['str_geom_column'] + \
              ", register.geom) AND boundary." + i_dict_boundary[
                'dict_boundary_dbtable']['str_condition_col'] + " = '" + \
              i_dict_boundary['dict_boundary_dbtable']['str_condition_val'] + "'"
      
    else:
        str_sql_statement_bound_cond = ""
        
    if str_sql_statement_bound_cond != "":
        
        #compose sql statement for register retrieval
        str_sql_statement = '''
          SELECT wp.*, adm.bez_nat, adm.bez_lan, adm.bez_krs 
          FROM (
              SELECT register.*, grid.gridcell_id, grid.x, grid.y 
              FROM ''' + \
                  i_dict_register_info['str_schema'] + "." + \
                  i_dict_register_info['str_data'] + " AS register, " + \
                  i_dict_weather_grid_info[
                    i_str_weather_dataset]['str_schema'] + '.' + \
                  i_dict_weather_grid_info[
                    i_str_weather_dataset]['str_data'] + " AS grid " + \
                  str_sql_statement_bound_src + \
              "WHERE inbetriebn IS NOT NULL AND ST_CONTAINS(grid." + \
              i_dict_weather_grid_info[i_str_weather_dataset][
                'str_geom_column'] + ", register.geom) " + \
              str_sql_statement_bound_cond + ") AS wp, " + \
              i_dict_boundary['dict_boundary_geodb']['str_schema'] + "." + \
              i_dict_boundary['dict_boundary_geodb']['str_data'] + " AS adm " +\
          '''WHERE ST_CONTAINS(adm.geom,wp.geom) AND
                   adm.bez_gem IS NOT NULL
          ORDER BY wp.gridcell_id;'''
        
        #print str_sql_statement
                 
        #retrieve register data
        try:
            cur_rli_db.execute(str_sql_statement)
            arr_register = [row for row in cur_rli_db.fetchall()]
            Info("Register successfully retrieved.", 1, dict_console_info)
            Info("Number of rows in register:   " + \
              str(len(arr_register)), 3, dict_console_info)
        except Exception as e:
            arr_error.append("Error: " + e.pgerror)
        else:  
            if arr_register == []:
                arr_error.append(
                  "Error: Selection of register data yielded no results!")
                  
        #print [x[15] for x in arr_register]
                  
        #compose sql statement for administration retrieval
        str_sql_statement = '''
          SELECT adm.bez_nat, adm.bez_lan, adm.bez_krs, adm.bez_gem 
          FROM (
              SELECT register.* 
              FROM ''' + i_dict_register_info['str_schema'] + "." + \
                  i_dict_register_info['str_data'] + " AS register" + \
                  str_sql_statement_bound_src + \
              "WHERE inbetriebn IS NOT NULL " + str_sql_statement_bound_cond + \
              ") AS wp, " + \
          i_dict_boundary['dict_boundary_geodb']['str_schema'] + \
            "." + i_dict_boundary['dict_boundary_geodb']['str_data'] + ''' AS adm 
          WHERE ST_CONTAINS(adm.geom,wp.geom) AND
                adm.bez_gem IS NOT NULL
          GROUP BY adm.bez_nat, adm.bez_lan, adm.bez_krs, adm.bez_gem;'''
        
        #print str_sql_statement
                 
        #retrieve administration data
        try:
            cur_rli_db.execute(str_sql_statement)
            arr_administration = [row for row in cur_rli_db.fetchall()]
            Info(
              "Administration areas successfully retrieved.", 1, dict_console_info)
            Info("Number of rows in administration areas:   " + \
              str(len(arr_administration)), 3, dict_console_info)
        except Exception as e:
            arr_error.append("Error: " + e.pgerror)
        else:  
            if arr_administration == []:
                arr_error.append(
                  "Error: Selection of administration data yielded no results!")
                  
    else:
        #compose sql statement for register retrieval
        str_sql_statement = '''
          SELECT register.*, grid.gridcell_id, grid.x, grid.y 
          FROM ''' + \
              i_dict_register_info['str_schema'] + "." + \
              i_dict_register_info['str_data'] + " AS register, " + \
              i_dict_weather_grid_info[
                i_str_weather_dataset]['str_schema'] + '.' + \
              i_dict_weather_grid_info[
                i_str_weather_dataset]['str_data'] + " AS grid " + \
              str_sql_statement_bound_src + \
          "WHERE inbetriebn IS NOT NULL AND ST_CONTAINS(grid." + \
          i_dict_weather_grid_info[i_str_weather_dataset][
            'str_geom_column'] + ", register.geom) " + \
          str_sql_statement_bound_cond + \
          "ORDER BY wp.gridcell_id;"
        
        #print str_sql_statement
                 
        #retrieve register data
        try:
            cur_rli_db.execute(str_sql_statement)
            arr_register = [row for row in cur_rli_db.fetchall()]
            Info("Register successfully retrieved.", 1, dict_console_info)
            Info("Number of rows in register:   " + \
              str(len(arr_register)), 3, dict_console_info)
        except Exception as e:
            arr_error.append("Error: " + e.pgerror)
        else:  
            if arr_register == []:
                arr_error.append(
                  "Error: Selection of register data yielded no results!")
                  
        #print [x[15] for x in arr_register]
              
    #compose sql statement for gridcell_id retrieval
    str_sql_statement = '''
      SELECT grid.gridcell_id, grid.x, grid.y 
      FROM ''' + \
          i_dict_register_info['str_schema'] + "." + \
          i_dict_register_info['str_data'] + " AS register, " + \
          i_dict_weather_grid_info[
            i_str_weather_dataset]['str_schema'] + '.' + \
          i_dict_weather_grid_info[
            i_str_weather_dataset]['str_data'] + " AS grid " + \
          str_sql_statement_bound_src + \
      "WHERE  inbetriebn IS NOT NULL AND ST_CONTAINS(grid." + \
        i_dict_weather_grid_info[i_str_weather_dataset][
          'str_geom_column'] +", register.geom) " + \
          str_sql_statement_bound_cond + \
      '''GROUP BY grid.gridcell_id, grid.x, grid.y  
      ORDER BY grid.gridcell_id;'''
    
    #print str_sql_statement
    
    #retrieve array of unique gridcell_ids
    try:
        cur_rli_db.execute(str_sql_statement)
        arr_gridcell_id = [row for row in cur_rli_db.fetchall()]
        Info("Gridcell Ids successfully retrieved.", 1, dict_console_info)
        Info("Number of unique gridcell_id: " + \
          str(len(arr_gridcell_id)), 3, dict_console_info)
    except Exception as e:
        arr_error.append("Error: " + e.pgerror)
    else:  
        if arr_gridcell_id == []:
            arr_error.append(
              "Error: Selection of gridcell_id data yielded no results!")
              
    #print [x[0] for x in arr_gridcell_id]
        
    #compose sql statement for power curves retrieval
    str_sql_statement = '''
      SELECT rli_anlagen_id, p_nenn, "1", "2", "3", "4", "5", "6", "7",
          "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", 
          "19", "20", "21", "22", "23", "24", "25" 
      FROM ''' + \
          i_dict_performance_curves_info['power_curves']['str_schema'] + "." +\
          i_dict_performance_curves_info['power_curves']['str_data'] + \
      ' WHERE "0" IS NOT NULL ORDER BY rli_anlagen_id'

    #retrieve power curve data
    try:
        cur_rli_db.execute(str_sql_statement)
        arr_P = [row for row in cur_rli_db.fetchall()]
    except Exception as e:
        arr_error.append("Error: " + e.pgerror)
    else:  
        if arr_P == []:
            arr_error.append(
              "Error: Selection of power curve data yielded no results!")

    #retrieve turbine type specific yearly shares
    if i_dict_powercurve_mix['source']['method'] == 'weighted_average':
        #compose sql statement for powercurves shares retrieval
        str_sql_statement = '''
          SELECT * 
          FROM ''' + \
              i_dict_powercurve_mix['source']['str_schema'] + "." +\
              i_dict_powercurve_mix['source']['str_data'] + \
          ' ORDER BY rli_anlagen_id'
        #retrieve powercurve shares data
        try:
            cur_rli_db.execute(str_sql_statement)
            arr_P_shares = [row for row in cur_rli_db.fetchall()]
            
        except Exception as e:
            arr_error.append("Error: " + e.pgerror)
    else:
        arr_P_shares = []
            
    #compose sql statement for cp curves retrieval
    str_sql_statement = '''
      SELECT 
          rli_anlagen_id, p_nenn, "1", "2", "3", "4", "5", "6", "7", "8", 
          "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", 
          "20", "21", "22", "23", "24", "25" 
      FROM ''' + \
          i_dict_performance_curves_info['cp_curves']['str_schema'] + \
          "." + i_dict_performance_curves_info['cp_curves']['str_data'] + \
      ' WHERE "0" IS NOT NULL ORDER BY rli_anlagen_id'
    
    #retrieve cp curve data
    try:
        cur_rli_db.execute(str_sql_statement)
        arr_cp = [row for row in cur_rli_db.fetchall()]
        Info("Performance curves successfully retrieved.", 1, dict_console_info)
        Info(
          "Number of cp-curves:    " + str(len(arr_cp)), 3, dict_console_info)
        Info("Number of Power-curves: " + str(len(arr_P)), 3, dict_console_info)
    except Exception as e:
        arr_error.append("Error: " + e.pgerror)
    else:  
        if arr_cp == []:
            arr_error.append(
              "Error: Selection of cp curve data yielded no results!")
            
    #compose sql statement for roughness length retrieval
    if i_dict_windspeed_corr['height_corr'] != 'linear':
        str_sql_statement = '''
          SELECT 
              grid.gridcell_id, z0.z0 
          FROM (
              SELECT grid.gridcell_id 
              FROM ''' + \
                  i_dict_register_info['str_schema'] + "." + \
                  i_dict_register_info['str_data'] + " AS register, " +\
                  i_dict_weather_grid_info[i_str_weather_dataset][
                    'str_schema'] + '.' + \
                  i_dict_weather_grid_info[i_str_weather_dataset][
                    'str_data'] + " AS grid " + str_sql_statement_bound_src + \
              "WHERE ST_CONTAINS(grid." + \
                i_dict_weather_grid_info[i_str_weather_dataset][
                  'str_geom_column'] +", register.geom) " + \
                str_sql_statement_bound_cond + \
              '''GROUP BY grid.gridcell_id) as grid 
          INNER JOIN ''' + \
              i_dict_z0_info['str_schema'] + "." + i_dict_z0_info['str_data'] +\
          ''' as z0 ON z0.gridcell_id = grid.gridcell_id 
          ORDER BY grid.gridcell_id;'''
        try:
            cur_rli_db.execute(str_sql_statement)
            arr_of_rows = [row for row in cur_rli_db.fetchall()]
            grid_cell_id = [x[0] for x in arr_of_rows]
            z_0 = [x[1] for x in arr_of_rows]
            arr_z0 = [grid_cell_id, z_0] #array of cols
            Info(
              "Roughness lengths successfully retrieved.",1, dict_console_info)
        except Exception as e:
            arr_error.append("Error: " + e.pgerror)
        else:  
            if arr_z0 == []:
                arr_error.append(
                  '''Error: 
                     Selection of roughness length data yielded no results!''')
                
        
    #retrieve random input (technical availability)
    if i_dict_random_input['bol_load'] == True:
        try:
            dict_random_input = loadmat(i_dict_random_input['str_load_path'])
            Info(
              "Timeseries of random input was retrieved.",1, dict_console_info)
              
        except:
            dict_random_input = {}
    
    if arr_error != []:
        print arr_error[0]
        
    return (arr_error, list(arr_register), list(arr_administration), 
            list(arr_gridcell_id), list(arr_cp), list(arr_P), 
            list(arr_P_shares), list(arr_z0), dict_random_input)
