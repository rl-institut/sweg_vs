#!/usr/bin/python
# -*- coding: utf-8 -*-
def sweg_vs_retrieve_weatherdata(
        arr_gridcell_id, i_str_weather_dataset, 
        i_dict_weather_dataset_info, hubheight_limits, i_dict_dates, 
        dict_console_info):
    '''    
    Loads and pre-processes ANEMOS or COSMO-DE weather data files..
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin 
     
    Keyword arguments:
        
        arr_gridcell_id -- array (3,1) containing information on id, x, y 
                           of one gridcell
        
        i_str_weather_dataset -- string specifying which dataset is to be used
        
        i_dict_weather_dataset_info -- dictionary containing information 
                                       on the weather datasets
        
        hubheight_limits -- array containing minimum and maximum hubheights of 
                            existing turbines in gridcell
        
        i_dict_dates -- dictionary containing information on time period to use
        
        dict_console_info -- dictionary containing information 
                             on the console logging functionality
    ''' 
    
    #import additional modules 
    import datetime
    import h5py
    import numpy as np
    
    from Modules.sweg_vs_additional_modules import console_info as Info
    from Modules.sweg_vs_additional_modules import loadmat
    from Modules.sweg_vs_additional_modules import create_timestamp_year
    from Modules.sweg_vs_additional_modules import matnum2datetime
    
    #declare local variables 
    arr_error = []
    arr_windspeed = []
    arr_winddirection = []
    arr_density = []
    #define start timestamp yyyy-mm-dd hh:mm from given initialization values 
    #yyyy-mm-dd first full hour of the first day
    start = datetime.datetime.combine(
      i_dict_dates['arr_date_period'][0], datetime.datetime.min.time()
    )
    #define end timestamp yyyy-mm-dd hh:mm from given initialization values 
    #yyyy-mm-dd: last full hour of the last day
    end = datetime.datetime.combine(
      i_dict_dates['arr_date_period'][1] + datetime.timedelta(days=1), 
      datetime.datetime.min.time()
    ) - datetime.timedelta(seconds=i_dict_weather_dataset_info[
      i_str_weather_dataset]['interval_minutes']*60)
    
    #weather dataset = ANEMOS
    if i_str_weather_dataset == "ANEMOS":
        
        arr_heights = [50, 100]
        arr_temperature = []
        #generate timestamps for ANEMOS dataset
        arr_timestamps_year = create_timestamp_year(
          i_dict_dates['arr_date_period'][0].year, 
          i_dict_weather_dataset_info[i_str_weather_dataset]['interval_minutes']
        )

        #add timestamp column to windspeed and temperature array
        arr_windspeed.append(arr_timestamps_year[
          arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
        ])
        arr_temperature.append(arr_timestamps_year[
          arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
        ])

        #compose path to windspeed data 50m
        str_anemos_path = \
          i_dict_weather_dataset_info[i_str_weather_dataset]['str_base_path'] + \
          i_dict_weather_dataset_info[i_str_weather_dataset][
            'str_path_prefix_windspeed'] + \
          str(i_dict_dates['arr_date_period'][0].year) + "/50m/" + \
          "%03d" % (arr_gridcell_id[1],) + "/Windspeed_50m_" + \
          "%03d" % (arr_gridcell_id[1],) + "_" + \
          "%03d" % (arr_gridcell_id[2],) + "_" + \
          str(i_dict_dates['arr_date_period'][0].year) + ".mat"
        
        #load data into variable
        arr_windspeed.append(
          loadmat(str_anemos_path)['v'][
            arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
          ]
        )

        #compose path to windspeed data 100m
        str_anemos_path = \
          i_dict_weather_dataset_info[i_str_weather_dataset]['str_base_path'] + \
          i_dict_weather_dataset_info[i_str_weather_dataset][
            'str_path_prefix_windspeed'] + \
          str(i_dict_dates['arr_date_period'][0].year) + "/100m/" + \
          "%03d" % (arr_gridcell_id[1],) + "/Windspeed_100m_" + \
          "%03d" % (arr_gridcell_id[1],) + "_" + \
          "%03d" % (arr_gridcell_id[2],) + "_" +\
          str(i_dict_dates['arr_date_period'][0].year) + ".mat"
        
        #load data into variable
        arr_windspeed.append(
          loadmat(str_anemos_path)['v'][
            arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
          ]
        )
        
        #compose path to temperature data 50m
        str_anemos_path = \
          i_dict_weather_dataset_info[i_str_weather_dataset]['str_base_path'] +\
          i_dict_weather_dataset_info[i_str_weather_dataset][
            'str_path_prefix_temperature'] + \
          str(i_dict_dates['arr_date_period'][0].year) + "/50m/" + \
          "%03d" % (arr_gridcell_id[1],) + "/Temperature_50m_" + \
          "%03d" % (arr_gridcell_id[1],) + "_" + \
          "%03d" % (arr_gridcell_id[2],) + "_" + \
          str(i_dict_dates['arr_date_period'][0].year) + ".mat"
        
        #load data into variable
        arr_temperature.append(
          loadmat(str_anemos_path)['T'][
            arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
          ]
        )
        
        #compose path to temperature data 100m
        str_anemos_path = \
          i_dict_weather_dataset_info[i_str_weather_dataset]['str_base_path'] +\
          i_dict_weather_dataset_info[i_str_weather_dataset][
            'str_path_prefix_temperature'] + \
          str(i_dict_dates['arr_date_period'][0].year) + "/100m/" + \
          "%03d" % (arr_gridcell_id[1],) + "/Temperature_100m_" + \
          "%03d" % (arr_gridcell_id[1],) + "_" + \
          "%03d" % (arr_gridcell_id[2],) + "_" + \
          str(i_dict_dates['arr_date_period'][0].year) + ".mat"
        
        #load data into variable
        arr_temperature.append(
          loadmat(str_anemos_path)['T'][
            arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
          ]
        )
        
        #temperature is masked as density, but is later treated as temperature
        arr_density = arr_temperature
        
    #weather dataset = COSMO-DE
    elif i_str_weather_dataset == "COSMO-DE":
        
        #Info("Weather data is beeing retrieved.",2, dict_console_info)
        #generate timestamps for COSMO-DE dataset
        arr_timestamps_year = create_timestamp_year(
          i_dict_dates['arr_date_period'][0].year, 
          i_dict_weather_dataset_info[
            i_str_weather_dataset]['interval_minutes']
        )

        
        #extract timestamps for calculation period
        arr_timestamps = arr_timestamps_year[
          arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
        ]
        
        #add timestamp column to windspeed and temperature array
        arr_windspeed.append(arr_timestamps_year[
          arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
        ])
        arr_density.append(arr_timestamps_year[
          arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
        ])
        arr_winddirection.append(arr_timestamps_year[
          arr_timestamps_year.index(start):arr_timestamps_year.index(end)+1
        ])
        
        #compose path COSMO-DE data file
        str_cosmode_path = \
          i_dict_weather_dataset_info[i_str_weather_dataset]['str_base_path'] + \
          "x" + str(arr_gridcell_id[1]) + "/" + "y" + \
          str(arr_gridcell_id[2]) + "/cosmode_x" + str(arr_gridcell_id[1]) + \
          "_y" + str(arr_gridcell_id[2]) + "_L39-50_" + \
          str(i_dict_dates['arr_date_period'][0].year) + ".mat"

        cosmo_vars = []
        
        cosmode_file = h5py.File(str_cosmode_path)
        #get array of all variables stored in the .mat file
        for i in range(len(cosmode_file['cosmo_vars'])):
            cosmo_vars.append(
              cosmode_file[
                cosmode_file[
                  'cosmo_vars'][i].item()].value.tostring().replace('\x00', '')
            )

        #get array of all height levels stored in the .mat file
        layers_data_m = cosmode_file['layers_data'].value[1]
        
        #get index of height levels < min_hubheight, height_levels_max_hubheight
        if hubheight_limits[0] != hubheight_limits[1]:
            nearest_height_index = [
              [
                abs(height_level - limit) 
                for height_level 
                in layers_data_m
              ].index(min([
                abs(height_level - limit) 
                for height_level 
                in layers_data_m
              ])) 
              for limit 
              in hubheight_limits
            ]
        else:
            nearest_height_index = [
              [
                abs(height_level - hubheight_limits[0]) 
                for height_level 
                in layers_data_m 
              ].index(min([
                abs(height_level - hubheight_limits[0]) 
                for height_level in layers_data_m]))
            ]
            arr_exclude = []
            arr_exclude.append(layers_data_m[nearest_height_index[0]])
            nearest_height_index.append([
              abs(height_level - hubheight_limits[0]) 
              for height_level 
              in layers_data_m
            ].index(min([
              abs(height_level - hubheight_limits[0]) 
              for height_level 
              in [
                x 
                for x 
                in layers_data_m 
                if x not in arr_exclude
              ]
            ])))

            nearest_height_index.sort()
            #closest index is not always index of wrapping height levels
            if hubheight_limits[0] < layers_data_m[nearest_height_index[0]] \
                    or hubheight_limits[0] > \
                    layers_data_m[nearest_height_index[1]]:
                if hubheight_limits[0] < layers_data_m[nearest_height_index[0]]:
                    arr_exclude.append(layers_data_m[nearest_height_index[1]])
                elif hubheight_limits[0] > layers_data_m[nearest_height_index[1]]:
                    arr_exclude.append(layers_data_m[nearest_height_index[0]])
                nearest_height_index = [
                  [
                    abs(height_level - hubheight_limits[0]) 
                    for height_level 
                    in layers_data_m 
                  ].index(min([
                    abs(height_level - hubheight_limits[0]) 
                    for height_level in layers_data_m]))
                ]
                nearest_height_index.append([
                  abs(height_level - hubheight_limits[0]) 
                  for height_level 
                  in layers_data_m
                ].index(min([
                  abs(height_level - hubheight_limits[0]) 
                  for height_level 
                  in [
                    x 
                    for x 
                    in layers_data_m 
                    if x not in arr_exclude
                  ]
                ])))
                
        #take only those height levels that are needed in calculation 
        #(min_hubheight < levels < max_hubheight)
        arr_heights = layers_data_m[
          nearest_height_index[0]:nearest_height_index[1]+1
        ]
        
        cosmo_data = cosmode_file['cosmo_data']
        
        #get cosmo-de timestamps, convert matlab timestamp to python timestamp 
        cosmo_timestamp = [
          i \
          for i \
          in [
            matnum2datetime(x) \
            for x \
            in cosmode_file['cosmo_timestamp'][0]
          ] if i != None
        ]
        
        #find indexes of missing timestamps
        missing_timestamp_idx = [
          arr_timestamps.index(step) \
          for step 
          in arr_timestamps 
          if step not in cosmo_timestamp
        ]
        
        for gap in missing_timestamp_idx:
            cosmo_timestamp.insert(gap, arr_timestamps[gap]) 
        
        #cosmo_data[height_level, variable, timestamps]
        for height in arr_heights:
            if missing_timestamp_idx != []:
                
                avg_windspeed = np.average(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('windh')]
                )
                avg_density = np.average(
                  cosmo_data[list(layers_data_m).index(height),
                             list(cosmo_vars).index('rho')]
                )
                avg_winddirection = np.average(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('dirh')]
                )
                
                arr_windspeed_tmp = list(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('windh')]
                )
                arr_density_tmp = list(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('rho')]
                )
                arr_winddirection_tmp = list(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('dirh')]
                )
                
                for gap in missing_timestamp_idx:
                    arr_windspeed_tmp.insert(gap, avg_windspeed) 
                    arr_density_tmp.insert(gap, avg_density) 
                    arr_winddirection_tmp.insert(gap, avg_winddirection) 
                    
                arr_windspeed.append(
                  arr_windspeed_tmp[
                    arr_timestamps_year.index(start):
                        arr_timestamps_year.index(end)+1
                  ]
                )
            
                arr_density.append(
                  arr_density_tmp[
                    arr_timestamps_year.index(start):
                        arr_timestamps_year.index(end)+1
                  ]
                )
            
                arr_winddirection.append(
                  arr_winddirection_tmp[
                    arr_timestamps_year.index(start):
                        arr_timestamps_year.index(end)+1
                  ]
                )
                    
            else:
                arr_windspeed.append(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('windh')][
                    arr_timestamps_year.index(start):
                        arr_timestamps_year.index(end)+1
                    ]
                )
            
                arr_density.append(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('rho')][
                    arr_timestamps_year.index(start):
                        arr_timestamps_year.index(end)+1
                    ]
                )
            
                arr_winddirection.append(
                  cosmo_data[list(layers_data_m).index(height), 
                             list(cosmo_vars).index('dirh')][
                    arr_timestamps_year.index(start):
                        arr_timestamps_year.index(end)+1
                    ]
                )

    if arr_error == []:
        Info("Weather data (windspeed, winddirection, density) successfully retrieved.", 
             2, dict_console_info)
        Info("Number of weather data values in time period: " + \
             str(len(arr_windspeed[0])), 3, dict_console_info)
    else:
        print arr_error[0]

    return arr_error, arr_windspeed, arr_density, arr_winddirection, arr_heights