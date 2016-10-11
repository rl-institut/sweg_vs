#!/usr/bin/python
# -*- coding: utf-8 -*-

def sweg_vs_calculate_electricity_generation(
        grid_cell, i_str_weather_dataset, i_dict_weather_dataset_info, 
        i_dict_dates, i_int_max_runtime_wec, arr_timestamp, arr_register_cell, 
        arr_cp, arr_P, arr_P_shares, z0, arr_windspeed, arr_winddirection, 
        arr_heights, i_dict_windspeed_corr, i_dict_windfarm_efficiencies, 
        i_dict_non_availabilities, arr_density, dict_random_input, 
        dict_console_info, ctrl_dict_charts, ctrl_dict_individual_results, 
        int_processor, i_dict_powercurve_mix, i_result_postprocessing):
    '''    
    Calculates unit specific electrical output as part of the SWEG module.
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin
        
    Keyword arguments:
        grid_cell -- integer number of current grid cell
    
        i_str_weather_dataset -- string indicating which weather dataset is used
        
        i_dict_weather_dataset_info -- dictionary containing information 
                                       on the weather datasets
                                       
        i_dict_dates -- dictionary containing information on time period to use
        
        i_int_max_runtime_wec -- integer defining typical runtime 
                                 of wind energy converters in years
        
        arr_timestamp -- array with timestamps of the period to be calculated
        
        arr_register_cell -- array containing all windturbines/windfarms 
                             in current grid cell
        
        arr_cp -- array containing cp values for all turbine types in database
        
        arr_P -- array containing Power values for all turbine types in database
        
        arr_P_shares -- array containing shares of turbine type numbers in 
                        different years
        
        z0 -- roughness length value for current gridcell
        
        arr_windspeed -- array of timestamps and horizontal windspeed data 
                         retrieved from weather dataset
                         
        arr_heights -- array containing nearest height levels
        
        arr_winddirection -- array of timestamps and horizontal wind direction 
                             data retrieved from weather dataset
        
        i_dict_windspeed_corr -- dictionary containing methods 
                                 for windspeed corrections
        
        i_dict_windfarm_efficiencies -- dictionary containing information 
                                        on how to calculate wind farm efficiency
                                        
        i_dict_non_availabilities -- dictionary containing details about the
                                     non-availabilities of units
        
        arr_density -- array of timestamps and temperature data retrieved 
                       from weather dataset
        
        dict_random_input -- dictionary containing 
                             existing technical availability data
        
        dict_console_info -- dictionary containing information 
                             on the console logging functionality
        
        ctrl_dict_charts -- dictionary controlling chart display
        
        ctrl_dict_individual_results -- dictionary controlling storage 
                                        of individual variables
        
        int_processor -- nr of processor
        
        i_dict_powercurve_mix -- dictionary containing information on the 
                                 method for power curve mixing
        
        i_result_postprocessing -- dictionary containing parameter for 
                                   postprocessing results
    ''' 
    
    #import additional modules 
    import datetime
    import math
    import numpy as np
    import random
    
    from Modules.sweg_vs_additional_modules import console_info as Info
    from Modules.sweg_vs_additional_modules import create_timestamp_year
    from Modules.sweg_vs_additional_modules import plot_values
    
    #define local functions
    def Density(
            arr_timestamp, arr_density, anlagen_nabenhoehe, 
            i_str_weather_dataset):
        '''Calculates density at hubheight for given weather data set.'''
        rho = []
        if i_str_weather_dataset == "ANEMOS":
            #density calculation with standard air pressure and dry air
            #standard pressure
            p = 101325 #Pa
            #specific gas constant
            R_s = 287.058 #J/(kg*k)
            '''rho = [
              p / (R_s * np.interp(
                [anlagen_nabenhoehe], 
                [50, 100], 
                [arr_density[1][i], arr_density[2][i]]
              )) 
              for i in range(len(arr_timestamp))
            ]'''
            for timestep in arr_timestamp:
                #arr_density is in fact arr_temperature
                #temperature gradient will be assumed as linear
                T_50 = arr_density[1][arr_density[0].index(timestep)]
                T_100 = arr_density[2][arr_density[0].index(timestep)]
                T = (T_100 - T_50)/50 * float(anlagen_nabenhoehe) + \
                    2 * T_50 - T_100 #K
                #print T
                rho.append(p / (R_s * T)) #kg/m³
            rho = np.array(rho)
            
        elif i_str_weather_dataset == "COSMO-DE":
            #linear interpolation of density between two altitude levels
            #rho calculation for each timestep or for all timesteps in arr_timestamp at once? 3D Interpolation?
            #rho = [np.interp([anlagen_nabenhoehe],arr_heights, [x[arr_density[0].index(timestep)] for x in arr_density[1:]])[0] for timestep in arr_timestamp]
            rho = [
              np.interp(
                [anlagen_nabenhoehe], 
                arr_heights, 
                [x[i] for x \
                in arr_density[1:]]
              )[0] 
              for i \
              in range(len(arr_timestamp))
            ]

        Info("Density was calculated!", 2, dict_console_info)
        return np.array(rho)
        
    def WindspeedCorrection(
            arr_timestamp, anlagen_nabenhoehe, arr_windspeed, z0, 
            i_dict_windspeed_corr):
        '''Calculates wind speed at hubheight.'''
        # height correction of windspeed
        if i_dict_windspeed_corr['height_corr'] == 'linear':
            #linear interpolation
            v_hubheight = [
              np.interp(
                [anlagen_nabenhoehe], 
                arr_heights, 
                [x[i] for x \
                in arr_windspeed[1:]]
              )[0] 
              for i \
              in range(len(arr_timestamp))
            ]
            
        elif i_dict_windspeed_corr['height_corr'] == 'logarithmic':
            #find altitude_level_m closest to anlagen_nabenhoehe
            #find index of nearest height in height_levels_m
            nearest_height_index = [
              abs(height_level - anlagen_nabenhoehe) \
              for height_level 
              in arr_heights].index(min([
                abs(height_level - anlagen_nabenhoehe) \
                for height_level \
                in arr_heights
              ]))
            
            #print nearest_height_index
            nearest_height = arr_heights[nearest_height_index]
            v_nearest_height = \
              np.array(arr_windspeed[nearest_height_index + 1])
            
            Info("Windspeeds @ nearest height " + \
              str(nearest_height) +"m : " + \
              str(v_nearest_height), 3, dict_console_info)
            #logarithmic correction
            v_hubheight = v_nearest_height * \
              ((math.log(anlagen_nabenhoehe/z0)) / \
              (math.log(nearest_height/z0)))
            
        Info("Windspeeds @ hubheight " + str(anlagen_nabenhoehe) + \
          "m : " + str(v_hubheight), 3, dict_console_info)
        
        Info("Windspeed was calculated!", 2, dict_console_info)
        
        return np.array(v_hubheight)
        
    def GenerateMixedPowerCurve(
            arr_type, arr_P_shares, arr_p_nenn_np, i_dict_powercurve_mix):
        '''Averages mixed power curves from a set of scaled power curves.'''
        if i_dict_powercurve_mix['method'] == 'average':
            arr_p_nenn_np = [
              np.average([
                float(x[i]) \
                for x \
                in arr_p_nenn_np \
              ]) 
              for i \
              in range(len(arr_p_nenn_np[0]))
            ]
        elif i_dict_powercurve_mix['method'] == \
                'weighted_average':
            #get indexes of scaled rli_anlagen_id
            arr_P_shares_index = [
              [
                x[list(i_dict_powercurve_mix[
                  'source']['arr_structure']).index('rli_anlagen_id')] 
                for x 
                in arr_P_shares
              ].index(i) 
              for i 
              in arr_type
              if i in [
                x[list(i_dict_powercurve_mix[
                  'source']['arr_structure']).index('rli_anlagen_id')] 
                for x 
                in arr_P_shares
              ]
            ]
            #if data for calculating weights exists, calculate weighted average
            #otherwise calculate normal average
            if arr_P_shares_index != []:
                 #get column index for year before current year
                year_ref = [
                  i.replace(' ', '')[i.index('_') + 1:] 
                  for i 
                  in list(i_dict_powercurve_mix['source']['arr_structure'])
                ].index(
                  str(i_dict_dates['arr_date_period'][0].year - 1)
                  )
                #determine weights array, 
                #set weights of unknown shares as mean of relevant shares
                mean_weight = np.average(
                    [float(arr_P_shares[i][year_ref]) for i in arr_P_shares_index]
                  )
            
                arr_weights = [
                  arr_P_shares[
                    [
                      x[
                        list(i_dict_powercurve_mix[
                          'source']['arr_structure']).index('rli_anlagen_id')
                      ] 
                    for x 
                    in arr_P_shares
                    ].index(t)
                  ][year_ref]
                  if t 
                  in [
                    arr_P_shares[s][list(i_dict_powercurve_mix[
                      'source']['arr_structure']).index('rli_anlagen_id')] 
                    for s 
                    in arr_P_shares_index
                  ]
                  else mean_weight
                  for t 
                  in arr_type]

                #calculate weighted average
                arr_p_nenn_np = [
                  np.average([
                    float(x[i]) \
                    for x \
                    in arr_p_nenn_np \
                  ], weights=arr_weights) 
                  for i \
                  in range(len(arr_p_nenn_np[0]))
                ]
            else:
                arr_p_nenn_np = [
                  np.average([
                    float(x[i]) \
                    for x \
                    in arr_p_nenn_np \
                  ]) 
                  for i \
                  in range(len(arr_p_nenn_np[0]))
                ]
                
        return arr_p_nenn_np
        
    def SelectPerformanceCurve(
            p_nenn, anlagen_name, anlagen_rotordm, arr_cp, arr_P, arr_P_shares):
        '''Selects power curve for specified rated capacity and anlagen_name.'''
        #check if which performance curve exists for current anlagen_name
        #print p_nenn, anlagen_name, anlagen_rotordm
        arr_cp_np = [0 for x in range(26)]
        arr_p_nenn_np = [0 for x in range(26)]
        
        if anlagen_name in [x[0] for x in arr_P]:
            #get index of anlagen_name in power curve table
            P_index = [x[0] for x in arr_P].index(anlagen_name)
            #get Power values belonging to anlagen_name
            arr_p_nenn_np = [float(x) for x in arr_P[P_index][2:] if x != None]
            anlagen_rotordm = float(anlagen_rotordm)
            #calculate cp curve from power curve assuming standard conditions
            arr_cp_np = np.array(arr_p_nenn_np) * 8000 / (np.array([
              float(x ** 3) \
              for x \
              in range(1,len(arr_p_nenn_np) + 1)
            ]) * 1.225 * math.pi * anlagen_rotordm ** 2)
        elif anlagen_name in [x[0] for x in arr_cp]:
            #get index of anlagen_name in cp-curve table
            cp_index = [x[0] for x in arr_cp].index(anlagen_name)
            #get cp-values belonging to anlagen_name
            arr_cp_np = [x for x in arr_cp[cp_index][2:] if x != None]
            anlagen_rotordm = float(anlagen_rotordm)
            #calculate Power curve from cp-curve assuming standard conditions
            arr_p_nenn_np =  np.array([
              x ** 3 \
              for x \
              in range(1,len(arr_cp_np) + 1)
            ]) * np.array([
              float(x) \
              for x \
              in arr_cp_np
            ]) * 1.225 * math.pi * anlagen_rotordm ** 2  / 8000
        else:
            #when no cp or power curve exists for anlagen_name
            #1st check for identical p_nenn
            arr_p_nenn_np = [
              list(x[2:]) \
              for x \
              in arr_P \
              if p_nenn == x[1] and 0 not in x[13:]
            ]
            arr_type = list([
              x[0] \
              for x \
              in arr_P \
              if p_nenn == x[1] and 0 not in x[13:]
            ])
            #2nd check for p_nenn +- 100 kW
            if arr_p_nenn_np == []:
                arr_p_nenn = [
                  list(x[2:]) \
                  for x \
                  in arr_P \
                  if abs(x[1] - p_nenn) < 100 and 0 not in x[13:]
                ]
                arr_type = list([
                      x[0] \
                      for x \
                      in arr_P \
                      if abs(x[1] - p_nenn) < 100 and 0 not in x[13:]
                ])
                #3rd check for p_nenn +- 500 kW
                if arr_p_nenn == []:
                    arr_p_nenn = [
                      list(x[2:]) \
                      for x \
                      in arr_P \
                      if abs(x[1] - p_nenn) < 500 and 0 not in x[13:]
                    ]
                    arr_type = list([
                      x[0] \
                      for x \
                      in arr_P \
                      if abs(x[1] - p_nenn) < 500 and 0 not in x[13:]
                    ])
                    if arr_p_nenn == []:
                        #4th check for p_nenn +- 1500 kW
                        arr_p_nenn = [
                          list(x[2:]) \
                          for x \
                          in arr_P \
                          if abs(x[1] - p_nenn) < 1500 and 0 not in x[13:]
                        ]
                        arr_type = list([
                          x[0] \
                          for x \
                          in arr_P \
                          if abs(x[1] - p_nenn) < 1500 and 0 not in x[13:]
                        ])
                        #scaling all power curves to current p_nenn
                        arr_p_nenn_np = [
                          x / max(x) * p_nenn \
                          for x \
                          in np.array(arr_p_nenn)]
                        #averaging all power curves
                        arr_p_nenn_np = GenerateMixedPowerCurve(
                            arr_type, arr_P_shares, arr_p_nenn_np,
                            i_dict_powercurve_mix)
                    else:
                        #scaling all power curves to current p_nenn
                        arr_p_nenn_np = [
                          x / max(x) * p_nenn \
                          for x \
                          in np.array(arr_p_nenn)
                        ]
                        #averaging all power curves
                        arr_p_nenn_np = GenerateMixedPowerCurve(
                            arr_type, arr_P_shares, arr_p_nenn_np,
                            i_dict_powercurve_mix)
                else:
                    #scaling all power curves to current p_nenn
                    arr_p_nenn_np = [
                      x / max(x) * p_nenn \
                      for x \
                      in np.array(arr_p_nenn)
                    ]
                    #averaging all power curves
                    arr_p_nenn_np = GenerateMixedPowerCurve(
                        arr_type, arr_P_shares, arr_p_nenn_np,
                        i_dict_powercurve_mix)
            else:
                #print arr_p_nenn
                arr_p_nenn_np = GenerateMixedPowerCurve(
                    arr_type, arr_P_shares, arr_p_nenn_np,
                    i_dict_powercurve_mix)
            #print arr_p_nenn_np
            arr_p_nenn_np = [float(x) for x in arr_p_nenn_np]
            anlagen_rotordm = float(anlagen_rotordm)
            #calculate cp curve from mean power curve under standard conditions
            arr_cp_np = np.array(arr_p_nenn_np) * 8000 / (np.array([
              float(x ** 3) \
              for x \
              in range(1,len(arr_p_nenn_np) + 1)
            ]) * 1.225 * math.pi * anlagen_rotordm ** 2)
            #interpolate power curve
  
        Info("Performance curve selected.",2,dict_console_info)           
        
        return arr_cp_np, arr_p_nenn_np
        
    def DetermineTechnicalAvailability(
            arr_availability, arr_timestamp, inbetriebn, i_int_max_runtime_wec, 
            dict_random_input, dict_console_info, dict_generation_key):  
        '''Generates unit specific annual time series of availability.'''
    
        if dict_random_input == {}:
        
            #for each windturbine the non-availability periods are determined 
            #using probability values for typical failures 
            #and the corresponding downtimes
            dict_failure_component = \
              i_dict_non_availabilities['technical']['Component']
            dict_failure_1000outof = [
              int(round(1 / x * 1000,0)) \
              for x \
              in i_dict_non_availabilities['technical']['FailureRate']
            ]
            dict_failure_downtimehours = \
              i_dict_non_availabilities['technical']['DowntimeHours']
            
            #recalculate timestamp interval in minutes
            interval = \
              (arr_availability[0][1] - arr_availability[0][0]).seconds / 60
            
            #initialize variables
            arr_result_period = [] 
            
            #extract timeperiod from arr_availability
            arr_result_period.append(
              arr_availability[0][
                arr_availability[0].index(arr_timestamp[0]):\
                arr_availability[0].index(arr_timestamp[-1]) + 1])
            
            Info("Calculating the technical availability.", 2, 
                 dict_console_info)
        
            for wec in range(0, len(arr_availability[-1])):
                #assign downtime due to failure
                for failure in range(len(dict_failure_1000outof)):
                    #determine wether failure occurs
                    if random.sample(xrange(
                      dict_failure_1000outof[failure]),1)[0] in range(1000):
                        #determine when failure occurs
                        int_start_index = random.sample(
                          xrange(len(arr_availability[0])),1)[0]
                        int_duration = int(
                          dict_failure_downtimehours[failure] * 60 / interval)
                        #if duration longer than period, shorten duration
                        if int_start_index + int_duration > \
                                len(arr_availability[0]):
                            int_duration = \
                              len(arr_availability[0]) - int_start_index
                        #set times of non-availability to zero
                        arr_availability[-1][wec][
                          int_start_index:(int_start_index + int_duration)] = \
                            [0 for k in range(int_duration)]
                        Info("Turbine " + str(wec + 1) + ": Failure of " + \
                             str(dict_failure_component[failure]) + \
                             ", Start: " + str(int_start_index) + \
                             ", Duration: " + str(int_duration) + \
                             "hrs", 3, dict_console_info)
        
                #assing downtime due to maintenance
                #first maintenance in first half year 
                #on two consecutive working days (Mo-Fr) during working hours 
                #(starting from 9 am) for 6 hours
                while 1:
                    int_start_index = random.sample(
                      xrange(9, 
                             int(round(len(
                               arr_availability[0])/2,0)), 
                             24 * 60 / interval
                      ),
                      1
                    )[0]
                    if (arr_availability[0][1] + \
                            datetime.timedelta(
                              days=int_start_index)).weekday() <= 3:
                        int_duration = int(6 * 60 / interval)
                        arr_availability[-1][wec][
                          int_start_index:(int_start_index + int_duration)] = \
                            [0 for k in range(int_duration)]
                        Info("Turbine " + str(wec + 1) + \
                             " 1st Maintenance, Start: " + \
                             str(int_start_index) + ", Duration: 2x" + \
                             str(int_duration) + "hrs", 3, dict_console_info)
                        #set start_index for second day of maintenance
                        int_start_index = int(
                          int_start_index + 24 * 60 / interval)
                        arr_availability[-1][wec][
                          int_start_index:(int_start_index + int_duration)] = \
                            [0 for k in range(int_duration)]
                        break

                #second maintenance between 160 and 182 days later 
                #on two consecutive working days (Mo-Fr) 
                #during working hours for 6 hours
                while 1:
                    int_start_index_2 = int(
                      int_start_index + random.sample([
                        x * 24 \
                        for x \
                        in range(160,182)
                      ], 
                      1)[0] * 60 / interval
                    )
                    #chose earlier start_index for 2nd maintenance 
                    #if within the last two weeks of the year
                    if (arr_availability[0][1] + \
                            datetime.timedelta(
                              days=int_start_index_2)).weekday() <= 3 and \
                        int_start_index_2 + int_duration + \
                        (24 + 336) * 60 / interval < len(arr_availability[0]):
                        
                        arr_availability[-1][wec][int_start_index_2:(
                          int_start_index_2 + int_duration)] = [
                            0 for k in range(int_duration)]
                        #set start_index for second day of maintenance
                        int_start_index_2 = int(
                          int_start_index_2 + 24 * 60 / interval)
                        arr_availability[-1][wec][int_start_index_2:(
                          int_start_index_2 + int_duration)] = \
                            [0 for k in range(int_duration)]
                        Info("Turbine " + str(wec + 1) + \
                             " 2nd Maintenance, Start: " + \
                             str(int_start_index_2) + ", Duration: 2x" + \
                             str(int_duration) + "hrs", 3, dict_console_info)
                        break
                
                #additional non-availabilities
                for event in \
                        range(i_dict_non_availabilities['misc']['Frequency']):
                    #determine wether non-availability occurs
                    if random.sample(
                            xrange(int(round(
                              1 / i_dict_non_availabilities['misc']['Rate'] * \
                              1000,0))
                            ), 
                            1)[0] in range(1000):
                        #determine when non-availability occurs
                        int_start_index = \
                          random.sample(xrange(len(arr_availability[0])),1)[0]
                        int_duration = int(
                          i_dict_non_availabilities['misc']['DowntimeHours'] * \
                            60 / interval)
                        if int_start_index + \
                                int_duration > len(arr_availability[0]):
                            int_duration = len(
                              arr_availability[0]) - int_start_index
                        arr_availability[-1][wec][
                          int_start_index:(int_start_index + int_duration)] = \
                            [0 for k in range(int_duration)]
                        Info("Turbine " + str(wec + 1) + \
                             ": Misc Non_Availability, Start: " + \
                             str(int_start_index) + ", Duration: " + \
                             str(int_duration) + "hrs", 3, dict_console_info)
                
                flo_technical_availability = round(float(sum(
                  arr_availability[-1][wec])) / \
                  float(len(arr_availability[0])),3) * 100
                
                Info("Technical Availability " + \
                     str(arr_availability[0][0].year)  + ": " + \
                     str(flo_technical_availability) + "%", 
                     3, dict_console_info)
                
                #add inbetriebn and maximum runtime constraints to arr_availability
                try:
                    inbetriebn_index = arr_availability[0].index(
                      datetime.datetime.combine(
                        inbetriebn, datetime.datetime.min.time()))
                    arr_availability[-1][wec][:inbetriebn_index] = [
                      0 for null in range(inbetriebn_index)]
                except ValueError:
                    pass
                try:
                    maximum_runtime_index = arr_availability[0].index(
                      datetime.datetime.combine(
                        inbetriebn, datetime.datetime.min.time()) + \
                        datetime.timedelta(days=i_int_max_runtime_wec * 365))
                    arr_availability[-1][wec][maximum_runtime_index:] = [
                      0 for null 
                      in range(len(
                        arr_availability[0]) - maximum_runtime_index)]
                except ValueError:
                    pass
                
                #clip the period of the year from the availability array, 
                #for which calculations are to be made
                arr_result_period.append(arr_availability[-1][wec][
                  arr_availability[0].index(arr_timestamp[0]): \
                  arr_availability[0].index(arr_timestamp[-1]) + 1])
                
            #calculate the cummulative availability for the whole wind farm
            arr_result_period = [
              sum([
                col[x] 
                for col 
                in arr_result_period[1:]
              ]) 
              for x 
              in range(len(arr_result_period[0]))
            ]
        else:
            arr_result_period = \
              dict_random_input[dict_generation_key]['availability']
#            arr_result_period = \
#              dict_random_input[dict_generation_key[
#                :dict_generation_key.index('_') + 1]]['availability']
    
        return arr_result_period

        
    def InterpolatePerformanceCurve(v, rho, arr_p_nenn_np, flh_factor):
        '''Interpolates density corrected power curve.'''
        
        #define standard wind speeds for each performance curve: 
        #performance curve values were retrieved for wind speeds 1...25 m/s
        v_std = np.array(range(1,26))
        if i_dict_windspeed_corr['density_corr'] == 'IEC_2006':
            P = [
              np.interp(
                v[i], 
                v_std * flh_factor * (1.225 / rho[i])**0.333333333, 
                arr_p_nenn_np, 
                left=0, 
                right = 0
              ) 
              for i \
              in range(len(v))
            ]
        elif i_dict_windspeed_corr['density_corr'] == 'WindPro_2010': 
            P = [
              np.interp(
                v[i], 
                v_std * flh_factor * (1.225 / rho[i])**(
                  np.interp(v_std,[7.5, 12.5], [0.333333333, 0.666666667])
                ), 
                arr_p_nenn_np, 
                left=0, 
                right = 0
              ) 
              for i 
              in range(len(v))
            ]
        Info("Power @ current windspeed: " + str(P),3,dict_console_info)

        return P
    
    def DetermineWindfarmEfficiency(
            arr_timestamp, wp_total_anz, i_dict_windfarm_efficiencies, 
            arr_v, arr_p_nenn_np):
        '''Determines wind farm efficiency.'''
        
        if i_dict_windfarm_efficiencies['method'] == "constant":
            windfarm_efficiency_min = [
              i_dict_windfarm_efficiencies['constant'] 
              for timestep 
              in arr_timestamp
            ]
        elif i_dict_windfarm_efficiencies['method'] == "ideal_square_simple":
            #interpolate wind farm efficiency based on number of turbines in
            #wind farm, scale minimum efficiencies to maximum 1
            windfarm_efficiency_min = np.interp(
              int(wp_total_anz), 
              i_dict_windfarm_efficiencies[
                'ideal_square_simple']['min_efficiencies'][0], 
                np.array([
                  i * i_dict_windfarm_efficiencies['ideal_square_simple'][
                    'factor'] 
                  if i * i_dict_windfarm_efficiencies['ideal_square_simple'][
                    'factor'] <= 1
                  else i
                  for i 
                  in i_dict_windfarm_efficiencies[
                    'ideal_square_simple']['min_efficiencies'][1]
                ]),
                left=1, 
                right = i_dict_windfarm_efficiencies[
                'ideal_square_simple']['min_efficiencies'][1][-1] * \
                i_dict_windfarm_efficiencies['ideal_square_simple']['factor']       
            )      
            
        #find cut-in- and rated-output-windspeed
        v_cutin = arr_p_nenn_np.index(min([
          x \
          for x \
          in arr_p_nenn_np \
          if x != 0
        ]))
        v_rated = arr_p_nenn_np.index(max([
          x \
          for x \
          in arr_p_nenn_np \
          if x != 0 and arr_p_nenn_np.index(x) <= 16
        ]))  
        
        if i_dict_windfarm_efficiencies['v_dependency']['method'] == \
                "linear_1-min_eff-1":
            arr_windfarm_efficiency = np.interp(
              arr_v, [
                v_cutin, v_cutin + ((v_rated * i_dict_windfarm_efficiencies['v_dependency']['factor'] - v_cutin) / 2), 
                v_rated * i_dict_windfarm_efficiencies['v_dependency']['factor']
              ], 
              [1, windfarm_efficiency_min, 1]
            )
        elif i_dict_windfarm_efficiencies['v_dependency']['method'] == \
                "linear_min_eff-min_eff-1":
            arr_windfarm_efficiency = np.interp(
              arr_v, [
                v_cutin, v_cutin + ((v_rated * i_dict_windfarm_efficiencies['v_dependency']['factor'] - v_cutin) / 2), 
                v_rated * i_dict_windfarm_efficiencies['v_dependency']['factor']
              ], 
              [windfarm_efficiency_min, windfarm_efficiency_min, 1]
            )
            
        else:
            arr_windfarm_efficiency = windfarm_efficiency_min

        #print arr_windfarm_efficiency

        #for future improvements add dependency of wind farm efficiency on wind direction

        Info("Windfarm efficiency calculated.",3,dict_console_info)
        
        return np.array(arr_windfarm_efficiency)
        
    def ResultProcessing(
            anlagen_anz, availability, windfarm_efficiency, EPF, P, flh_factor):
                
        #print rli_wp_id, anlagen_anz, np.average(windfarm_efficiency), np.average(EPF)
        #print len(availability), len(windfarm_efficiency), len(EPF), len(cp), len(rho), len(v)
        Power_100 = anlagen_anz * windfarm_efficiency * EPF * P 
            
        Power_real = availability * windfarm_efficiency * EPF * P 
        
        #print rli_wp_id, anlagen_nabenhoehe, anlagen_anz, np.average(availability), np.average(windfarm_efficiency), np.average(EPF), sum(Power_real)
                        
        Info("Electrical Power Output: " + str(Power_real),
      	  3, dict_console_info)

        if 'full_load_hours' in i_result_postprocessing['method']:
            int_flh = float(sum(Power_real)) * \
              (i_dict_weather_dataset_info[
                i_str_weather_dataset]['interval_minutes'] / 60) / \
                (float(p_nenn) * float(anlagen_anz))
            if int_flh != 0:
                
                flh_min = float(i_result_postprocessing[
                  'flh_setup']['flh_min_mean_max'][0] * \
                  i_result_postprocessing['flh_setup']['wind_index'] / 100 * \
                  i_result_postprocessing['flh_setup']['flh_shares'][
                    bundesland][0]
                )
                
                flh_mean_left = float(i_result_postprocessing[
                  'flh_setup']['flh_min_mean_max'][1] * \
                  i_result_postprocessing['flh_setup']['wind_index'] / 100 * \
                  i_result_postprocessing['flh_setup']['flh_shares'][
                    bundesland][1] * i_result_postprocessing[
                      'flh_setup']['flh_mean_range'][0])
                  
                flh_mean = float(i_result_postprocessing[
                  'flh_setup']['flh_min_mean_max'][1] * \
                  i_result_postprocessing['flh_setup']['wind_index'] / 100 * \
                  i_result_postprocessing['flh_setup']['flh_shares'][
                    bundesland][1])
                  
                flh_mean_right = float(i_result_postprocessing[
                  'flh_setup']['flh_min_mean_max'][1] * \
                  i_result_postprocessing['flh_setup']['wind_index'] / 100 * \
                  i_result_postprocessing['flh_setup']['flh_shares'][
                    bundesland][1] * i_result_postprocessing[
                      'flh_setup']['flh_mean_range'][1])

                flh_max = float(i_result_postprocessing[
                  'flh_setup']['flh_min_mean_max'][2] * \
                  i_result_postprocessing['flh_setup']['wind_index'] / 100 * \
                  i_result_postprocessing['flh_setup']['flh_shares'][
                    bundesland][2]
                )
                      
                arr_x = [flh_min, flh_mean_left, flh_mean_right, flh_max]
                arr_y = [flh_min, flh_mean, flh_mean, flh_max]
                
                flh_target = np.interp(int_flh, arr_x, arr_y, left=flh_min, right=flh_max)
                
                #iterative power curve shifting until target value for
                #full load hours is achieved
                arr_flh = []
                arr_flh_factor = []
                
                for i in range(10):
                    if abs(int_flh - flh_target) < 10:
                        break
                    else:
                        if int_flh - flh_target > 0:
                            flh_factor += np.interp(
                              abs(int_flh - flh_target), [0,2000],[0, 0.5]
                            )
                            arr_flh_factor.append(flh_factor)
                        else:
                            flh_factor -= np.interp(
                              abs(int_flh - flh_target), [0,2000],[0, 0.5]
                            )
                            arr_flh_factor.append(flh_factor)
                        
                    #interpolate performance curve
                    P = InterpolatePerformanceCurve(v, rho, 
                                                    arr_p_nenn_np, 
                                                    flh_factor
                    )
                    Power_100 = anlagen_anz * windfarm_efficiency * EPF * P 
        
                    Power_real = availability * windfarm_efficiency * EPF * P 
                    int_flh = float(sum(Power_real)) * \
                      (i_dict_weather_dataset_info[
                        i_str_weather_dataset]['interval_minutes'] / 60) / \
                        (float(p_nenn) * float(anlagen_anz))
                    arr_flh.append(int_flh)
                    
                if abs(int_flh - flh_target) >= 10:
                    if int_flh > flh_target:
                        flh_factor = arr_flh_factor[arr_flh.index(min(arr_flh))]
                    else:
                        flh_factor = arr_flh_factor[arr_flh.index(max(arr_flh))]
                    P = InterpolatePerformanceCurve(v, rho, 
                                                    arr_p_nenn_np, 
                                                    flh_factor
                    )
                    Power_100 = anlagen_anz * windfarm_efficiency * EPF * P 
        
                    Power_real = availability * windfarm_efficiency * EPF * P 
                
                    int_flh = float(sum(Power_real)) * \
                      (i_dict_weather_dataset_info[
                        i_str_weather_dataset]['interval_minutes'] / 60) / \
                        (float(p_nenn) * float(anlagen_anz))
                    
                Info("Full-Load-Hour based correction applied.",
                 3, dict_console_info)
                 
        return Power_real, Power_100, flh_factor
        
    #begin of main code section  
    
    #declare local variables 
    arr_error = []
    arr_availability_year = []
    
    dict_generation = {}
    
    #create array for technical availability of each wind turbine
    arr_availability_year.append(
      create_timestamp_year(
        i_dict_dates['arr_date_period'][0].year, 
        i_dict_weather_dataset_info[i_str_weather_dataset]['interval_minutes']
      )
    )

    for wp in range(len(arr_register_cell)):
        #define variables
        rli_wp_id = arr_register_cell[wp][1].rstrip()
        inbetriebn = arr_register_cell[wp][3]
        anlagen_name = arr_register_cell[wp][4]
        anlagen_anz = arr_register_cell[wp][5]
        wp_total_anz = arr_register_cell[wp][14]
        p_nenn = arr_register_cell[wp][6]
        p_nenn_total = arr_register_cell[wp][7]
        anlagen_nabenhoehe = float(arr_register_cell[wp][8])
        anlagen_rotordm = arr_register_cell[wp][9]
        if 'full_load_hours' in i_result_postprocessing['method']:
            bundesland = arr_register_cell[wp][19]

        Info(str(rli_wp_id),2, dict_console_info)
        
        #reject all wind farms that were constructed in a later year
        if inbetriebn.year <= i_dict_dates['arr_date_period'][0].year:
            if anlagen_name != None:
                dict_generation_key = rli_wp_id + "_" + anlagen_name
            else:
                dict_generation_key = rli_wp_id + "_"
                
            #dict_generation_key = rli_wp_id + "_"
            dict_generation[dict_generation_key] = {}
            #dict_generation[dict_generation_key]['anlagen_name'] = anlagen_name
            dict_generation[dict_generation_key]['anlagen_nabenhoehe'] = \
              anlagen_nabenhoehe
            dict_generation[dict_generation_key]['anlagen_rotordm'] = \
              float(anlagen_rotordm)
            dict_generation[dict_generation_key]['p_nenn_total'] = \
              float(p_nenn_total)
          
            Info(str(int_processor) + " RLI Windpark ID: " + str(rli_wp_id),
                 2, dict_console_info)
            Info("Rated Power: " + str(int(anlagen_anz)) + "x " + \
                 str(p_nenn) + "kW, Turbine Type: " + str(anlagen_name),
                 3, dict_console_info)

            #prepare arr_availability
            arr_availability_year.append(
              [
                [
                  1 for i 
                  in range(len(arr_availability_year[0]))
                ] 
                for j 
                in range(anlagen_anz)
              ]
            )
            
            #height correction of windspeed
            v = WindspeedCorrection(
              arr_timestamp, 
              anlagen_nabenhoehe, 
              arr_windspeed, 
              z0, 
              i_dict_windspeed_corr
            )
            
            #calculate or interpolate density
            rho = Density(
              arr_timestamp, 
              arr_density, 
              anlagen_nabenhoehe, 
              i_str_weather_dataset
            )
            
            #select performance curve
            arr_cp_np, arr_p_nenn_np = SelectPerformanceCurve(
              p_nenn, 
              anlagen_name, 
              anlagen_rotordm, 
              arr_cp, 
              arr_P, 
              arr_P_shares
            )
            
            #interpolate performance curve
            flh_factor = i_dict_weather_dataset_info[
              i_str_weather_dataset]['power_curve_factor']
            P = InterpolatePerformanceCurve(v, rho, arr_p_nenn_np, flh_factor)
            
            #determine non-availability periods for each windturbine
            availability = DetermineTechnicalAvailability(
              arr_availability_year, 
              arr_timestamp, 
              inbetriebn, 
              i_int_max_runtime_wec, 
              dict_random_input, 
              dict_console_info, 
              dict_generation_key
            )

	    #windfarm_efficiency
            windfarm_efficiency = DetermineWindfarmEfficiency(
              arr_timestamp, 
              wp_total_anz, 
              i_dict_windfarm_efficiencies, 
              v, 
              list(arr_p_nenn_np)
            )
            
            #Energy Pattern Factor, accounting 
            #for the loss of energy due to averaged hourly values
            if i_dict_weather_dataset_info[
                    i_str_weather_dataset]['interval_minutes'] == 60:
                EPF = 1 + 0.2794 * v ** (-0.8674)
            else:
                EPF = 1
            
            anlagen_anz = float(anlagen_anz)
            anlagen_rotordm = float(anlagen_rotordm)
                 
            #postprocessing of results
            #full load hours
            Power_real, Power_100, flh_factor = ResultProcessing(anlagen_anz, 
              availability, windfarm_efficiency, EPF, P, flh_factor
            )
            
            #full load hour factor
            dict_generation[dict_generation_key]['flh_factor'] = [flh_factor]
                 
            #write results to dict_generation
            dict_generation[dict_generation_key]['operation_hours'] = \
              [len([
                x 
                for x 
                in Power_real 
                if x > 0
              ]) * \
              i_dict_weather_dataset_info[
                i_str_weather_dataset]['interval_minutes'] / 60
            ]
            #power curve
            dict_generation[dict_generation_key]['power_curve'] = [[0.0] + \
              list(arr_p_nenn_np)]
            #technical availability
            dict_generation[dict_generation_key]['availability'] = availability
            #windfarm efficiency
            dict_generation[dict_generation_key]['windfarm_efficiency'] = \
              windfarm_efficiency            
            if 'EPF' in ctrl_dict_individual_results:
                #Energy Pattern Factor
                dict_generation[dict_generation_key]['EPF'] = \
                  [round(x,3) for x in EPF]
            if 'P' in ctrl_dict_individual_results:
                #P
                dict_generation[dict_generation_key]['P'] =\
                  [round(x,3) for x in P]
            if 'rho' in ctrl_dict_individual_results:
                #rho
                dict_generation[dict_generation_key]['rho'] = \
                  [round(x,3) for x in rho]   
            if 'v' in ctrl_dict_individual_results:
                #v 
                dict_generation[dict_generation_key]['v'] = \
                  [round(x,3) for x in v]
            #100% technical availability
            dict_generation[dict_generation_key]['Power_100'] = \
              [round(x / 1000,3) for x in Power_100] 
            #real technical availability
            dict_generation[dict_generation_key]['Power_real'] = \
              [round(x / 1000,3) for x in Power_real]
            
            if 'Power_100_spec' in ctrl_dict_individual_results:
                #100% technical availability one average turbine
                dict_generation[dict_generation_key]['Power_100_spec'] = [
                  dict_generation[dict_generation_key]['Power_100'][i] / \
                    dict_generation[dict_generation_key]['availability'][i] 
                  for i 
                  in range(len(Power_100)) 
                  if availability[i] != 0
                ]
            if 'Power_real_spec' in ctrl_dict_individual_results:
                #real technical availability one average turbine
                dict_generation[dict_generation_key]['Power_real_spec'] = [
                  dict_generation[dict_generation_key]['Power_100'][i] / \
                    dict_generation[dict_generation_key]['availability'][i] 
                  for i 
                  in range(len(Power_real)) 
                  if availability[i] != 0
                ]
            if 'Power_loss' in ctrl_dict_individual_results:
                #difference between Power_100 and Power_real
                dict_generation[dict_generation_key]['Power_loss'] =  \
                  [round(x / 1000, 3) for x in (Power_100 - Power_real)]
            
            
            if ctrl_dict_charts['chart_per_windfarm'] == True and \
                    sum(Power_real) != 0:
                
                plot_values([
                  {
                    'subplot': 231, 
                    'plottype':"linepoint", 
                    'x_vals': range(1,len(arr_cp_np) + 1), 
                    'y_vals':arr_cp_np, 
                    'x_label': "windspeed", 
                    'y_label': "cp in [-]", 
                    'y_range': [0,0.6], 
                    'title': "cp-curve", 
                    'color': "#ff8822", 
                    'x_date': False
                  },
                  {
                    'subplot': 234, 
                    'plottype':"linepoint", 
                    'x_vals': range(1,len(arr_cp_np) + 1), 
                    'y_vals': arr_p_nenn_np, 
                    'x_label': "windspeed", 
                    'y_label': "P in kW", 
                    'y_range': [0], 
                    'title': "Power-curve", 
                    'color': "#ff00ff", 
                    'x_date': False
                  },
                  {
                    'subplot': 232, 
                    'plottype':"point", 
                    'x_vals': arr_timestamp, 
                    'y_vals': windfarm_efficiency, 
                    'x_label': "Time", 
                    'y_label': "[-]", 
                    'y_range': [], 
                    'title': "windfarm_efficiency", 
                    'color': "#00cc44", 
                    'x_date': True
                  },
                  {
                    'subplot': 235, 
                    'plottype':"point", 
                    'x_vals': arr_timestamp, 
                    'y_vals': availability, 
                    'x_label': "Time", 
                    'y_label': "[-]", 
                    'y_range': [], 
                    'title': "Availability", 
                    'color': "#cc7722", 
                    'x_date': True
                  },
                  {
                    'subplot': 233, 
                    'plottype':"point", 
                    'x_vals': arr_timestamp, 
                    'y_vals': v, 
                    'x_label': "Time", 
                    'y_label': "v in m/s", 
                    'y_range': [], 
                    'title': "v @ " + str(anlagen_nabenhoehe) + "m",
                    'color': "#1d6087", 
                    'x_date': True
                  }, 
                  {
                    'subplot': 236, 
                    'plottype':"bar", 
                    'x_vals': arr_timestamp, 
                    'y_vals': Power_real / 1000, 
                    'x_label': "Time", 
                    'y_label': "P in MW", 
                    'y_range': [], 
                    'title': "Electrical Output", 
                    'color': "#cc0000",
                    'x_date': True
                  }
                  ], 
                  str(int(anlagen_anz)) + "x " + str(anlagen_name) + " " +\
                    rli_wp_id + " (" + str(int(wp_total_anz)) + \
                    " WEC in Windpark)"
                )

    if ctrl_dict_charts['chart_per_grid_cell'] == True and \
            sum(Power_real) != 0:
        v = [
          np.average(
            [
              j[timestep] 
              for j 
              in [
                dict_generation[i]['v'] 
                for i 
                in [
                  k for k in dict_generation
                ] 
              ]
            ]
          ) 
          for timestep 
          in range(len(arr_timestamp))
        ]
        P_real = np.array(
          [
            np.sum([
              j[timestep] 
              for j 
              in [
                dict_generation[i]['Power_real'] 
                for i 
                in [
                  k 
                  for k 
                  in dict_generation
                ]
              ]
            ]) 
            for timestep 
            in range(len(arr_timestamp))
          ]
        ) 
        P_100 = np.array(
          [
            np.sum([
              j[timestep] 
              for j 
              in [
                dict_generation[i]['Power_100'] 
                for i in [
                  k 
                  for k 
                  in dict_generation
                ]
              ]
            ]) 
            for timestep 
            in range(len(arr_timestamp))
          ]
        )
        P_loss = np.array(
          [
            np.sum([
              j[timestep] 
              for j 
              in [
                dict_generation[i]['Power_loss'] 
                for i in [
                  k 
                  for k 
                  in dict_generation
                ]
              ]
            ]) 
            for timestep 
            in range(len(arr_timestamp))
          ]
        )
        Availability = np.array([
          np.sum(
            [
              j[timestep] 
              for j 
              in [
                dict_generation[i]['availability'] 
                for i 
                in [
                  k 
                  for k 
                  in dict_generation
                ]
              ]
            ]) 
            for timestep 
            in range(len(arr_timestamp))
          ]
        )

        plot_values([
          {
            'subplot': 321, 
            'plottype':"linepoint", 
            'x_vals': arr_timestamp, 
            'y_vals': v, 
            'x_label': "time", 
            'y_label': "windspeed in m/s", 
            'y_range': [], 
            'title': "Wind speed", 
            'color': "#1d6087", 
            'x_date': True
          },
          {
            'subplot': 323, 
            'plottype':"bar", 
            'x_vals': arr_timestamp, 
            'y_vals': P_100 , 
            'x_label': "Time", 
            'y_label': "P in MW", 
            'y_range': [], 
            'title': "Electrical Output 100%", 
            'color': "#cc0000", 
            'x_date': True
          },
          {
            'subplot': 325, 
            'plottype':"bar", 
            'x_vals': arr_timestamp, 
            'y_vals': P_real , 
            'x_label': "Time", 
            'y_label': "P in MW", 
            'y_range': [], 
            'title': "Electrical Output Real", 
            'color': "#cc0000", 
            'x_date': True
          },
          {
            'subplot': 322, 
            'plottype':"linepoint", 
            'x_vals': arr_timestamp, 
            'y_vals': v, 
            'x_label': "time", 
            'y_label': "windspeed in m/s", 
            'y_range': [], 
            'title': "Wind speed", 
            'color': "#1d6087", 
            'x_date': True
          },
          {
            'subplot': 324, 
            'plottype':"bar", 
            'x_vals': arr_timestamp, 
            'y_vals': Availability , 
            'x_label': "Time", 
            'y_label': "Turbines", 
            'y_range': [], 
            'title': "No of available Turbines", 
            'color': "#00cc44", 
            'x_date': True
          },
          {
            'subplot': 326, 
            'plottype':"point", 
            'x_vals': arr_timestamp, 
            'y_vals': P_loss, 
            'x_label': "Time", 
            'y_label': "P in kW", 
            'y_range': [], 
            'title': "Electrical Output Difference", 
            'color': "#ff00ff", 
            'x_date': True
          }
          ], "Gridcell " + str(grid_cell)
        )
    
    Info("Electricity generation for gridcell " + \
      str(grid_cell) + " successfully calculated.", 
      2, dict_console_info)
      
    return arr_error, dict_generation
