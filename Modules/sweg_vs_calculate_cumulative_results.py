#!/usr/bin/python
# -*- coding: utf-8 -*-

def sweg_vs_calculate_cumulative_results(dict_result, 
  ctrl_dict_cumulative_results, arr_register, i_str_weather_dataset, 
  i_dict_weather_dataset_info, arr_administration, i_result_postprocessing,
  dict_console_info):
    '''Calculates cumulative results on defined temporal and spatial levels
    from sweg_vs detailed results.
    
    Copyright (c)2013 Marcus Biank, Reiner Lemoine Institut, Berlin
    
    Keyword arguments:
    
    dict_result -- dictionary containing detailed results
    
    ctrl_dict_cumulative_results -- dictionary with temporal and spatial
                                    specifications
    
    arr_register -- array with register data used in the simulation
    
    i_str_weather_dataset -- string with name of used weather data set
    
    i_dict_weather_dataset_info -- dictionary with weather data set
                                   specifications
    
    arr_administration -- array with data on administration levels
    
    i_result_postprocessing --dictionary containing parameter for 
                              postprocessing results
    
    dict_console_info -- dictionary containing basic data for terminal plotting
    ''' 
    
    #import additional modules 
    import numpy as np
    
    from Modules.sweg_vs_additional_modules import console_info as Info
    
    #declare local variables 
    arr_error_calccum = []
    dict_cum_result = {}
    int_source_interval_min = \
      i_dict_weather_dataset_info[i_str_weather_dataset]['interval_minutes']
    arr_area_calculated = []
    
    arr_register = \
      [[x[i] for x in arr_register] for i in range(len(arr_register[0]))]
    arr_administration = [[x[i] for x in arr_administration] \
                         for i in range(len(arr_administration[0]))]
    
    #define local functions
    def cumresults_admin_none(adm_level, adm_col_nr, 
                              register_col_nr, int_source_interval_min):
        '''
        Calculates cumulative results for original timely resolution.
        '''
        for area in arr_administration[adm_col_nr]:
            if area not in arr_area_calculated:
                arr_area_calculated.append(area)
                dict_cum_result[adm_level][area] = {}
                for key,value in {'availability': 'availability', 
                                  'Power_real':'energy_real', 
                                  'Power_100':'energy_100'}.iteritems(): 
                    #get result values for current area       
                    tmp = [
                        x for x 
                        in [
                            [dict_result[gridcell]['generation'][wp][key]
                            for wp 
                            in dict_result[gridcell] 
                              ['generation'].iterkeys()
                            if area == arr_register[register_col_nr][
                              [idx for idx, elem 
                                in enumerate(arr_register[1]) 
                                if wp[:wp.index('_')] in elem][0]
                                ].rstrip()
                            ] 
                            for gridcell in dict_result.iterkeys() 
                            if gridcell != 'timestamp_python' and
                               gridcell != 'timestamp_matlab'
                        ]
                        if x != []
                    ]
                    
                    if key == 'availability':
                        dict_cum_result[adm_level][area][value] = np.array(
                          [sum([
                            x[i] 
                            for x in [item for sublist in tmp 
                              for item in sublist]
                          ]
                          )for i in range(len(tmp[0][0]))
                        ])
                        
                    else:
                        tmp_energy = np.array([sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]) 
                          for i 
                          in range(len(tmp[0][0]))
                        ]) * int_source_interval_min / 60
                        tmp_power = np.array([sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]) 
                          for i 
                          in range(len(tmp[0][0]))
                        ])
                        if ctrl_dict_cumulative_results[
                                'timeseries_format'] == "original":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_energy
                            dict_cum_result[adm_level][area][key] = tmp_power
                        elif ctrl_dict_cumulative_results[
                                'timeseries_format'] == "normalized":
                            #get cumulative rated capacity
                            p_rated = np.sum([
                                sum(x) 
                                for x 
                                in [
                                    [dict_result[gridcell][
                                      'generation'][wp]['p_nenn_total']
                                    for wp 
                                    in dict_result[gridcell] 
                                      ['generation'].iterkeys()
                                    if area == arr_register[register_col_nr][
                                      [idx for idx, elem 
                                        in enumerate(arr_register[1]) 
                                        if wp[:wp.index('_')] in elem][0]
                                        ].rstrip()
                                    ]
                                    for gridcell in dict_result.iterkeys() 
                                    if gridcell != 'timestamp_python' and
                                       gridcell != 'timestamp_matlab'
                                ]
                                if x != []
                            ]) / 1000
                            dict_cum_result[adm_level][area][value] = \
                              tmp_energy / (
                                p_rated * int_source_interval_min / 60)
                            dict_cum_result[adm_level][area][key] = \
                              tmp_power / p_rated

        return dict_cum_result
        
    def cumresults_admin_hour(adm_level, adm_col_nr, 
                              register_col_nr, int_source_interval_min, 
                              int_target_interval_min):
        '''
        Calculates cumulative results for hourly timely resolution.
        '''
        for area in arr_administration[adm_col_nr]:
            if area not in arr_area_calculated:
                arr_area_calculated.append(area)
                dict_cum_result[adm_level][area] = {}
                for key,value in {'availability': 'availability', 
                                  'Power_real':'energy_real', 
                                  'Power_100':'energy_100'}.iteritems(): 
                    #get result values for current area       
                    tmp = [
                      x 
                      for x 
                      in [
                        [
                          dict_result[gridcell]['generation'][wp][key] 
                          for wp 
                          in dict_result[gridcell]['generation'].iterkeys() 
                          if area == arr_register[register_col_nr][
                            [
                              idx 
                              for idx, elem 
                              in enumerate(arr_register[1]) 
                              if wp[:wp.index('_')] 
                              in elem
                            ][0]
                          ].rstrip()
                        ] 
                        for gridcell 
                        in dict_result.iterkeys() 
                        if gridcell != 'timestamp_python' 
                        and gridcell != 'timestamp_matlab'
                      ] 
                      if x != []
                    ]
                    if key == 'availability':
                        tmp_availability = [
                          np.average(
                            [
                              sum(
                                [
                                  x[i] 
                                  for x 
                                  in [
                                    item 
                                    for sublist 
                                    in tmp 
                                    for item 
                                    in sublist
                                  ]
                                ]
                              ) 
                              for i 
                              in range(len(tmp[0][0]))
                            ][v:(v + int_target_interval_min / \
                                int_source_interval_min)
                            ]
                          ) 
                          for v 
                          in range(0, len(tmp[0][0]), 
                                   int_target_interval_min / \
                                   int_source_interval_min
                          )
                        ]
                        if ctrl_dict_cumulative_results[
                                'timeseries_format'] == "original":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_availability
                        elif ctrl_dict_cumulative_results[
                                'timeseries_format'] == "normalized":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_availability / max(tmp_availability)
                    else:
                        tmp_energy = np.array(
                          [
                            np.sum(
                              [
                                sum(
                                  [
                                    x[i] 
                                    for x 
                                    in [
                                      item 
                                      for sublist 
                                      in tmp 
                                      for item 
                                      in sublist
                                    ]
                                  ]
                                ) 
                                for i 
                                in range(len(tmp[0][0]))
                              ][v:(v + int_target_interval_min / \
                                int_source_interval_min)
                              ]
                            ) 
                            for v 
                            in range(0, len(tmp[0][0]), 
                                     int_target_interval_min / \
                                     int_source_interval_min
                            )
                          ]
                        ) * int_source_interval_min / 60
                        tmp_power = [
                          np.average(
                            [
                              sum(
                                [
                                  x[i] 
                                  for x 
                                  in [
                                    item 
                                    for sublist 
                                    in tmp 
                                    for item 
                                    in sublist
                                  ]
                                ]
                              ) 
                              for i 
                              in range(len(tmp[0][0]))
                            ][v:(v + int_target_interval_min / \
                              int_source_interval_min)
                            ]
                          ) 
                          for v 
                          in range(0, len(tmp[0][0]), 
                                   int_target_interval_min / \
                                   int_source_interval_min
                          )
                        ] 
                        if ctrl_dict_cumulative_results[
                                'timeseries_format'] == "original":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_energy
                            dict_cum_result[adm_level][area][key] = tmp_power
                        elif ctrl_dict_cumulative_results[
                                'timeseries_format'] == "normalized":
                            #get cumulative rated capacity
                            p_rated = np.sum([
                                sum(x) for x 
                                in [
                                    [dict_result[gridcell][
                                      'generation'][wp]['p_nenn_total']
                                    for wp 
                                    in dict_result[gridcell] 
                                      ['generation'].iterkeys()
                                    if area == arr_register[register_col_nr][
                                      [idx for idx, elem 
                                        in enumerate(arr_register[1]) 
                                        if wp[:wp.index('_')] in elem][0]
                                        ].rstrip()
                                    ] 
                                    for gridcell in dict_result.iterkeys() 
                                    if gridcell != 'timestamp_python' and
                                       gridcell != 'timestamp_matlab'
                                ]
                                if x != []
                            ]) / 1000
                            dict_cum_result[adm_level][area][value] = \
                              tmp_energy / p_rated
                            dict_cum_result[adm_level][area][key] = \
                              tmp_power / p_rated
        return dict_cum_result
                
    def cumresults_admin_day(adm_level, adm_col_nr, 
                             register_col_nr, int_source_interval_min, 
                             int_target_interval_min):
        '''
        Calculates cumulative results for daily timely resolution.
        '''
        for area in arr_administration[adm_col_nr]:
            if area not in arr_area_calculated:
                arr_area_calculated.append(area)
                dict_cum_result[adm_level][area] = {}
                for key,value in {'availability': 'availability', 
                                  'Power_real':'energy_real', 
                                  'Power_100':'energy_100'}.iteritems(): 
                    #get result values for current area                 
                    tmp = [
                      x 
                      for x 
                      in [
                        [
                          dict_result[gridcell]['generation'][wp][key] 
                          for wp 
                          in dict_result[gridcell]['generation'].iterkeys() 
                          if area == arr_register[register_col_nr][
                            [
                              idx 
                              for idx, elem 
                              in enumerate(arr_register[1]) 
                              if wp[:wp.index('_')] 
                              in elem][0]].rstrip()
                        ] 
                        for gridcell 
                        in dict_result.iterkeys() 
                        if gridcell != 'timestamp_python' 
                        and gridcell != 'timestamp_matlab'
                      ] if x != []
                    ]
                    if key == 'availability':
                        tmp_availability = [
                          np.average(
                            [
                              sum(
                                [
                                  x[i] 
                                  for x 
                                  in [
                                    item 
                                    for sublist 
                                    in tmp 
                                    for item 
                                    in sublist
                                  ]
                                ]
                              ) 
                              for i 
                              in range(len(tmp[0][0]))
                            ][v:(v + int_target_interval_min / \
                              int_source_interval_min)
                            ]
                          ) 
                          for v 
                          in range(0, len(tmp[0][0]), 
                                   int_target_interval_min / \
                                   int_source_interval_min
                          )
                        ]
                        if ctrl_dict_cumulative_results[
                                'timeseries_format'] == "original":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_availability
                        elif ctrl_dict_cumulative_results[
                                'timeseries_format'] == "normalized":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_availability / max(tmp_availability)
                    else:
                        tmp_energy = np.array(
                          [
                            np.sum(
                              [
                                sum(
                                  [
                                    x[i] for 
                                    x in [
                                      item 
                                      for sublist 
                                      in tmp 
                                      for item 
                                      in sublist
                                    ]
                                  ]
                                ) 
                                for i 
                                in range(len(tmp[0][0]))
                              ][v:(v + int_target_interval_min / \
                                int_source_interval_min)
                              ]
                            ) 
                            for v 
                            in range(0, len(tmp[0][0]), 
                                     int_target_interval_min / \
                                     int_source_interval_min
                            )
                          ]
                        ) * int_source_interval_min / 60
                        tmp_power = [
                          np.average(
                            [
                              sum(
                                [
                                  x[i] 
                                  for x 
                                  in [
                                    item 
                                    for sublist 
                                    in tmp 
                                    for item 
                                    in sublist
                                  ]
                                ]
                              ) 
                              for i 
                              in range(len(tmp[0][0]))
                            ][v:(v + int_target_interval_min / \
                              int_source_interval_min)
                            ]
                          ) 
                          for v 
                          in range(0, len(tmp[0][0]), 
                                   int_target_interval_min / \
                                   int_source_interval_min
                          )
                        ] 
                        if ctrl_dict_cumulative_results[
                                'timeseries_format'] == "original":
                            dict_cum_result[adm_level][area][value] = \
                              tmp_energy
                            dict_cum_result[adm_level][area][key] = tmp_power
                        elif ctrl_dict_cumulative_results[
                                'timeseries_format'] == "normalized":
                            #get cumulative rated capacity
                            p_rated = np.sum([
                                sum(x) for x 
                                in [
                                    [dict_result[gridcell][
                                      'generation'][wp]['p_nenn_total']
                                    for wp 
                                    in dict_result[gridcell] 
                                      ['generation'].iterkeys()
                                    if area == arr_register[register_col_nr][
                                      [idx for idx, elem 
                                        in enumerate(arr_register[1]) 
                                        if wp[:wp.index('_')] in elem][0]
                                        ].rstrip()
                                    ] 
                                    for gridcell in dict_result.iterkeys() 
                                    if gridcell != 'timestamp_python' and
                                       gridcell != 'timestamp_matlab'
                                ]
                                if x != []
                            ]) / 1000
                            dict_cum_result[adm_level][area][value] = \
                              tmp_energy / (p_rated * 24)
                            dict_cum_result[adm_level][area][key] = \
                              tmp_power / p_rated
        return dict_cum_result
        
    def cumresults_admin_period(adm_level, adm_col_nr, register_col_nr):
        '''
        Calculates cumulative results for complete period.
        '''
        for area in arr_administration[adm_col_nr]:
            if area not in arr_area_calculated:
                arr_area_calculated.append(area)
                dict_cum_result[adm_level][area] = {}
                for key,value in {'availability': 'availability', 
                                  'Power_real':'energy_real', 
                                  'Power_100':'energy_100'}.iteritems(): 
                    #get result values for current area    
                    tmp = [
                      x 
                      for x 
                      in [
                        [
                          dict_result[gridcell]['generation'][wp][key] 
                          for wp 
                          in dict_result[gridcell]['generation'].iterkeys() 
                          if area == arr_register[register_col_nr][
                            [
                              idx 
                              for idx, elem 
                              in enumerate(arr_register[1]) 
                              if wp[:wp.index('_')] in elem
                            ][0]
                          ].rstrip()
                        ] 
                        for gridcell 
                        in dict_result.iterkeys() 
                        if gridcell != 'timestamp_python' 
                        and gridcell != 'timestamp_matlab' 
                      ] 
                      if x != []
                    ]
                    #print tmp
                    if key == 'availability':
                        dict_cum_result[adm_level][area][value] = [
                          np.average(
                            [
                              sum(
                                [
                                  x[i] 
                                  for x 
                                  in [
                                    item 
                                    for sublist 
                                    in tmp 
                                    for item 
                                    in sublist
                                  ]
                                ]
                              ) 
                              for i 
                              in range(len(tmp[0][0]))
                            ]
                          )
                        ]
                    else:
                        tmp_energy = np.sum(
                          [
                            sum(
                              [
                                x[i] 
                                for x 
                                in [
                                  item 
                                  for sublist 
                                  in tmp 
                                  for item 
                                  in sublist
                                ]
                              ]
                            ) 
                            for i 
                            in range(len(tmp[0][0]))
                          ]
                        ) * int_source_interval_min / 60
                        tmp_power = np.average(
                          [
                            sum(
                              [
                                x[i] 
                                for x 
                                in [
                                  item 
                                  for sublist 
                                  in tmp 
                                  for item 
                                  in sublist
                                ]
                              ]
                            ) 
                            for i 
                            in range(len(tmp[0][0]))
                          ]
                        )
                        dict_cum_result[adm_level][area][value] = [tmp_energy]
                        dict_cum_result[adm_level][area][key] = [tmp_power]
        return dict_cum_result        
        
 
    
    Info('Cumulative Results are being calculated...', 1, dict_console_info)
    
    ctrl_dict_cumulative_results['cumulation_level_space'] = [
      str(x).rstrip() 
      for x 
      in ctrl_dict_cumulative_results['cumulation_level_space']
    ]
    
    dict_cum_result['desc'] = {"timestamp_python": "-", 
                               "timestamp_matlab":"-", 
                               "availability": "wec", 
                               "Power_real": "MW", 
                               "Energy_real": "MWh", 
                               "Power_100":"MW", 
                               "Energy_100": "MWh"
    }
    dict_cum_result['comments'] = {"Variables":[
      "Power_real and Power_100 always represent average power for respective time interval"
    ]}
     
    #creating timestamps based on target intervalls
    if ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
        dict_cum_result['timestamp_python'] = [
          x 
          for x 
          in dict_result['timestamp_python'] 
          if (x - dict_result['timestamp_python'][0]).seconds % 3600 == 0]
        dict_cum_result['timestamp_matlab'] = [
          d.strftime("%d-%b-%Y %H:%M:%S") 
          for d 
          in dict_cum_result['timestamp_python']
        ]
    elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
        dict_cum_result['timestamp_python'] = [
          x.date() 
          for x 
          in dict_result['timestamp_python'] 
          if (x - dict_result['timestamp_python'][0]).seconds % 86400 == 0]
        dict_cum_result['timestamp_matlab'] = [
          d.strftime("%d-%b-%Y") 
          for d 
          in dict_cum_result['timestamp_python']
        ]
    elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
        dict_cum_result['timestamp_python'] = [
          str(dict_result['timestamp_python'][0]) + " - " + \
          str(dict_result['timestamp_python'][-1])
        ]
        dict_cum_result['timestamp_matlab'] = \
          dict_cum_result['timestamp_python']
    elif ctrl_dict_cumulative_results['cumulation_level_time'] == "None":
        dict_cum_result['timestamp_python'] = dict_result['timestamp_python']
        dict_cum_result['timestamp_matlab'] = [
          d.strftime("%d-%b-%Y %H:%M:%S") 
          for d 
          in dict_cum_result['timestamp_python']
        ]
        
    #"Boundary" or "Land" or "Bundesland" or "Regierungsbezirk" 
    #or "Kreis" or "Verwaltungsgemeinschaft" or "Gemeinde" or "Windpark"
    if "Boundary" in ctrl_dict_cumulative_results['cumulation_level_space']:
        dict_cum_result['boundary'] = {}
        
        #calculate hourly output values
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "None":
            dict_cum_result['boundary'] = {}
            for key,value in {'availability': 'availability', 
                              'Power_real':'energy_real', 
                              'Power_100':'energy_100'}.iteritems(): 
                #get result values for current area       
                tmp = [
                  [
                    dict_result[gridcell]['generation'][wp][key] 
                    for wp 
                    in dict_result[gridcell]['generation'].iterkeys()
                  ] 
                  for gridcell 
                  in dict_result.iterkeys() 
                  if gridcell != 'timestamp_python' 
                  and gridcell != 'timestamp_matlab' 
                ]
                if key == 'availability':
                    dict_cum_result['boundary'][value] = np.array(
                      [
                        np.sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]
                        ) 
                        for i 
                        in range(len(tmp[0][0]))
                      ]
                    )
                else:
                    tmp_energy = np.array(
                      [
                        np.sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]
                        ) 
                        for i 
                        in range(len(tmp[0][0]))
                      ]
                    ) * int_source_interval_min / 60
                    tmp_power = np.array(
                      [
                        np.sum(
                          [
                            x[i] 
                            for x in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]
                        ) 
                        for i 
                        in range(len(tmp[0][0]))
                      ]
                    )
                    if ctrl_dict_cumulative_results[
                            'timeseries_format'] == "original":
                        dict_cum_result['boundary'][value] = tmp_energy
                        dict_cum_result['boundary'][key] = tmp_power
                    elif ctrl_dict_cumulative_results[
                            'timeseries_format'] == "normalized":
                        #get cumulative rated capacity
                        p_rated = np.sum([
                          sum([
                            dict_result[gridcell]['generation'][wp][key] 
                            for wp 
                            in dict_result[gridcell]['generation'].iterkeys()
                          ]) 
                          for gridcell 
                          in dict_result.iterkeys() 
                          if gridcell != 'timestamp_python' 
                          and gridcell != 'timestamp_matlab' 
                        ]) / 1000
                        dict_cum_result['boundary'][value] = \
                          tmp_energy / (p_rated * int_source_interval_min / 60)
                        dict_cum_result['boundary'][key] = \
                          tmp_power / p_rated
        
        #calculate hourly output values
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
            int_target_interval_min = 60
            for key,value in  {'availability': 'availability', 
                               'Power_real':'energy_real', 
                               'Power_100':'energy_100'}.iteritems(): 
                tmp = [
                  [
                    dict_result[gridcell]['generation'][wp][key] 
                    for wp 
                    in dict_result[gridcell]['generation'].iterkeys()] 
                    for gridcell 
                    in dict_result.iterkeys() 
                    if gridcell != 'timestamp_python'
                    and gridcell != 'timestamp_matlab' 
                  ][0]
                if key == 'availability':
                    dict_cum_result['boundary'][value] = [
                      np.average(
                        [
                          sum(
                            [
                              x[i] 
                              for x 
                              in [
                                item 
                                for sublist 
                                in tmp 
                                for item 
                                in sublist
                              ]
                            ]
                          ) 
                          for i 
                          in range(len(tmp[0][0]))
                        ][v:(v + int_target_interval_min / \
                          int_source_interval_min)
                        ]
                      ) 
                      for v 
                      in range(0, len(tmp[0][0]), 
                               int_target_interval_min / \
                               int_source_interval_min
                      )
                    ]
                else:
                    tmp_energy = np.array(
                      [
                        np.sum(
                          [
                            sum(
                              [
                                x[i] 
                                for x 
                                in [
                                  item 
                                  for sublist 
                                  in tmp 
                                  for item 
                                  in sublist
                                ]
                              ]
                            ) 
                            for i 
                            in range(len(tmp[0][0]))
                          ][v:(v + int_target_interval_min / \
                            int_source_interval_min)
                          ]
                        ) 
                        for v 
                        in range(0, len(tmp[0][0]), 
                                 int_target_interval_min / \
                                 int_source_interval_min
                        )
                      ]
                    ) * int_source_interval_min / 60
                    tmp_power = [
                      np.average(
                        [
                          sum(
                            [
                              x[i] 
                              for x 
                              in [
                                item 
                                for sublist 
                                in tmp 
                                for item 
                                in sublist
                              ]
                            ]
                          ) 
                          for i 
                          in range(len(tmp[0][0]))
                        ][v:(v + int_target_interval_min / \
                          int_source_interval_min)
                        ]
                      ) 
                      for v 
                      in range(0, len(tmp[0][0]), 
                               int_target_interval_min / \
                               int_source_interval_min
                      )
                    ] 
                    if ctrl_dict_cumulative_results[
                            'timeseries_format'] == "original":
                        dict_cum_result['boundary'][value] = tmp_energy
                        dict_cum_result['boundary'][key] = tmp_power
                    elif ctrl_dict_cumulative_results[
                            'timeseries_format'] == "normalized":
                        #get cumulative rated capacity
                        p_rated = np.sum([
                          sum([
                            dict_result[gridcell]['generation'][wp][key] 
                            for wp 
                            in dict_result[gridcell]['generation'].iterkeys()
                          ])
                          for gridcell 
                          in dict_result.iterkeys() 
                          if gridcell != 'timestamp_python' 
                          and gridcell != 'timestamp_matlab'
                        ]) / 1000
                        dict_cum_result['boundary'][value] = \
                          tmp_energy / p_rated
                        dict_cum_result['boundary'][key] = \
                          tmp_power / p_rated
 
        #calculate daily output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
            int_target_interval_min = 24 * 60
            for key,value in  {'availability': 'availability', 
                               'Power_real':'energy_real', 
                               'Power_100':'energy_100'}.iteritems(): 
                tmp = [
                  [
                    dict_result[gridcell]['generation'][wp][key]
                    for wp 
                    in dict_result[gridcell]['generation'].iterkeys()
                  ] 
                  for gridcell 
                  in dict_result.iterkeys() 
                  if gridcell != 'timestamp_python' 
                  and gridcell != 'timestamp_matlab'
                ][0]
                if key == 'availability':
                    dict_cum_result['boundary'][value] = [
                      np.average(
                        [
                          sum(
                            [
                              x[i] 
                              for x 
                              in [
                                item 
                                for sublist 
                                in tmp 
                                for item 
                                in sublist
                              ]
                            ]
                          ) 
                          for i 
                          in range(len(tmp[0][0]))
                        ][v:(v + int_target_interval_min / \
                          int_source_interval_min)
                        ]
                      ) 
                      for v 
                      in range(0, len(tmp[0][0]), 
                               int_target_interval_min / \
                               int_source_interval_min
                      )
                    ]
                else:
                    tmp_energy = np.array(
                      [
                        np.sum(
                          [
                            sum(
                              [
                                x[i] 
                                for x 
                                in [
                                  item 
                                  for sublist 
                                  in tmp 
                                  for item 
                                  in sublist
                                ]
                              ]
                            ) 
                            for i 
                            in range(len(tmp[0][0]))
                          ][v:(v + int_target_interval_min / \
                            int_source_interval_min)
                          ]
                        ) 
                        for v 
                        in range(0, len(tmp[0][0]), 
                                 int_target_interval_min / \
                                 int_source_interval_min
                        )
                      ]
                    ) * int_source_interval_min / 60
                    tmp_power = [
                      np.average(
                        [
                          sum(
                            [
                              x[i] 
                                for x 
                                in [
                                  item 
                                  for sublist 
                                  in tmp 
                                  for item 
                                  in sublist
                                ]
                              ]
                            ) 
                            for i 
                            in range(len(tmp[0][0]))
                          ][v:(v + int_target_interval_min / \
                            int_source_interval_min)
                          ]
                        ) 
                        for v 
                        in range(0, len(tmp[0][0]), 
                                 int_target_interval_min / \
                                 int_source_interval_min
                      )
                    ] 
                    if ctrl_dict_cumulative_results[
                            'timeseries_format'] == "original":
                        dict_cum_result['boundary'][value] = tmp_energy
                        dict_cum_result['boundary'][key] = tmp_power
                    elif ctrl_dict_cumulative_results[
                            'timeseries_format'] == "normalized":
                        #get cumulative rated capacity
                        p_rated = np.sum([
                          sum([
                            dict_result[gridcell]['generation'][wp][key] 
                            for wp 
                            in dict_result[gridcell]['generation'].iterkeys()
                          ])
                          for gridcell 
                          in dict_result.iterkeys() 
                          if gridcell != 'timestamp_python' 
                          and gridcell != 'timestamp_matlab'
                        ]) / 1000
                        dict_cum_result['boundary'][value] = \
                          tmp_energy / (p_rated * 24)
                        dict_cum_result['boundary'][key] = \
                          tmp_power / p_rated
            
        #calculate a single output value for the whole period
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
            int_target_interval_min = (
              dict_result['timestamp_python'][-1] - \
              dict_result['timestamp_python'][0]
            ).total_seconds() / 60
            for key,value in  {'availability': 'availability', 
                               'Power_real':'energy_real', 
                               'Power_100':'energy_100'}.iteritems(): 
                tmp = [
                  [
                    dict_result[gridcell]['generation'][wp][key] 
                    for wp 
                    in dict_result[gridcell]['generation'].iterkeys()
                  ] 
                  for gridcell
                  in dict_result.iterkeys() 
                  if gridcell != 'timestamp_python' 
                  and gridcell != 'timestamp_matlab' 
                ][0]
                if key == 'availability':
                    dict_cum_result['boundary'][value] = np.average(
                      [
                        sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]
                        ) 
                        for i
                        in range(len(tmp[0][0]))
                      ]
                    )
                else:
                    tmp_energy = np.sum(
                      [
                        sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]
                        ) 
                        for i 
                        in range(len(tmp[0][0]))
                      ]
                    ) * int_source_interval_min / 60
                    tmp_power = np.average(
                      [
                        sum(
                          [
                            x[i] 
                            for x 
                            in [
                              item 
                              for sublist 
                              in tmp 
                              for item 
                              in sublist
                            ]
                          ]
                        ) 
                        for i 
                        in range(len(tmp[0][0]))
                      ]
                    )
                    dict_cum_result['boundary'][value] = tmp_energy
                    dict_cum_result['boundary'][key] = tmp_power


    if "Land" in ctrl_dict_cumulative_results['cumulation_level_space']:
        adm_level = 'land'
        adm_col_nr = 0
        register_col_nr = 18
        dict_cum_result[adm_level] = {}
               
        #calculate output values at original timely resolution
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "None":
            dict_cum_result = cumresults_admin_none(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min
            ) 
       
        #calculate hourly output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
            int_target_interval_min = 60
            dict_cum_result = cumresults_admin_hour(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate daily output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
            int_target_interval_min = 24 * 60
            dict_cum_result = cumresults_admin_day(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate a single output value for the whole period
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
            int_target_interval_min = (
              dict_result['timestamp_python'][-1] - \
              dict_result['timestamp_python'][0]).total_seconds() / 60
            dict_cum_result = cumresults_admin_period(
              adm_level, adm_col_nr, register_col_nr
            ) 
            
    if "Bundesland" in ctrl_dict_cumulative_results['cumulation_level_space']:
        adm_level = 'bundesland'
        adm_col_nr = 1
        register_col_nr = 19
        dict_cum_result[adm_level] = {}
        
        
        #calculate output values at original timely resolution
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "None":
            dict_cum_result = cumresults_admin_none(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min
            )
        
        #calculate hourly output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
            int_target_interval_min = 60
            dict_cum_result = cumresults_admin_hour(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate daily output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
            int_target_interval_min = 24 * 60
            dict_cum_result = cumresults_admin_day(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate a single output value for the whole period
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
            int_target_interval_min = (dict_result['timestamp_python'][-1] - \
              dict_result['timestamp_python'][0]).total_seconds() / 60
            dict_cum_result = cumresults_admin_period(
              adm_level, adm_col_nr, register_col_nr
            ) 
            
    if  "Kreis" in ctrl_dict_cumulative_results['cumulation_level_space']:
        adm_level = "kreis"
        adm_col_nr = 2
        register_col_nr = 20
        dict_cum_result[adm_level] = {}
        
        #calculate output values at original timely resolution
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "None":
            dict_cum_result = cumresults_admin_none(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min
            )
        
        #calculate hourly output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
            int_target_interval_min = 60
            dict_cum_result = cumresults_admin_hour(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate daily output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
            int_target_interval_min = 24 * 60
            dict_cum_result = cumresults_admin_day(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate a single output value for the whole period
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
            int_target_interval_min = (dict_result['timestamp_python'][-1] - \
              dict_result['timestamp_python'][0]).total_seconds() / 60
            dict_cum_result = cumresults_admin_period(
              adm_level, adm_col_nr, register_col_nr
            ) 
            
        #print dict_cum_result[adm_level]
            
    if "Gemeinde" in ctrl_dict_cumulative_results['cumulation_level_space']:
        adm_level = "gemeinde"
        adm_col_nr = 3
        register_col_nr = 2
        dict_cum_result[adm_level] = {}
        
        #calculate output values at original timely resolution
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "None":
            dict_cum_result = cumresults_admin_none(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min
            )
        
        #calculate hourly output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
            int_target_interval_min = 60
            dict_cum_result = cumresults_admin_hour(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            )
            
        #calculate daily output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
            int_target_interval_min = 24 * 60
            dict_cum_result = cumresults_admin_day(
              adm_level, adm_col_nr, register_col_nr, int_source_interval_min, 
              int_target_interval_min
            ) 
            
        #calculate a single output value for the whole period
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
            int_target_interval_min = (dict_result['timestamp_python'][-1] - \
              dict_result['timestamp_python'][0]).total_seconds() / 60
            dict_cum_result = cumresults_admin_period(
              adm_level, adm_col_nr, register_col_nr
            ) 
        
    
    if "Windpark" in ctrl_dict_cumulative_results['cumulation_level_space']:
        adm_level = "windpark"
        dict_cum_result[adm_level] = {}
        
        #calculate hourly output values
        if ctrl_dict_cumulative_results['cumulation_level_time'] == "Hour":
            int_target_interval_min = 60
            for gridcell in [
                    x 
                    for x 
                    in dict_result.iterkeys() 
                    if x != 'timestamp_python' 
                    and x != 'timestamp_matlab' 
                    ]:
                for wp in [
                        x 
                        for x 
                        in dict_result[gridcell]['generation'].iterkeys()]:
                    dict_cum_result[adm_level][wp] = {}
                    for key,value in {'availability': 'availability', 
                                      'Power_real':'energy_real', 
                                      'Power_100':'energy_100'}.iteritems():  
                        tmp = [
                          [
                            x 
                            for x 
                            in [
                              dict_result[gridcell]['generation'][wp][key]
                            ]
                          ]
                        ]
                        if key == 'availability':
                            tmp_availability = [
                              np.average(
                                [
                                  sum(
                                    [
                                      x[i] 
                                      for x 
                                      in [
                                        item 
                                        for sublist 
                                        in tmp 
                                        for item 
                                        in sublist
                                      ]
                                    ]
                                  ) 
                                  for i 
                                  in range(len(tmp[0][0]))
                                ][v:(v + int_target_interval_min / \
                                  int_source_interval_min)
                                ]
                              ) 
                              for v 
                              in range(0, len(tmp[0][0]), 
                                       int_target_interval_min / \
                                       int_source_interval_min
                              )
                            ]
                            if ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "original":
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_availability
                            elif ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "normalized":
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_availability / max(tmp_availability)
                        else:
                            tmp_energy = np.array(
                              [
                                np.sum(
                                  [
                                    sum(
                                      [
                                        x[i]
                                        for x 
                                        in [
                                          item 
                                          for sublist 
                                          in tmp 
                                          for item 
                                          in sublist
                                        ]
                                      ]
                                    ) 
                                    for i 
                                    in range(len(tmp[0][0]))
                                  ][v:(v + int_target_interval_min / \
                                    int_source_interval_min)
                                  ]
                                ) 
                                for v 
                                in range(0, len(tmp[0][0]), 
                                         int_target_interval_min / \
                                         int_source_interval_min
                                )
                              ]
                            ) * int_source_interval_min / 60
                            tmp_power = [
                              np.average(
                                [
                                  sum(
                                    [
                                      x[i] 
                                      for x 
                                      in [
                                        item 
                                        for sublist 
                                        in tmp 
                                        for item 
                                        in sublist
                                      ]
                                    ]
                                  ) 
                                  for i 
                                  in range(len(tmp[0][0]))
                                ][v:(v + int_target_interval_min / \
                                  int_source_interval_min)
                                ]
                              ) 
                              for v 
                              in range(0, len(tmp[0][0]), 
                                       int_target_interval_min / \
                                       int_source_interval_min
                              )
                            ] 
                            if ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "original":
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_energy
                                dict_cum_result[adm_level][wp][key] = tmp_power
                            elif ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "normalized":
                                p_rated = float(dict_result[gridcell][
                                  'generation'][wp]['p_nenn_total']) / 1000
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_energy / p_rated
                                dict_cum_result[adm_level][wp][key] = \
                                  tmp_power / p_rated
            
        #calculate daily output values
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Day":
            int_target_interval_min = 24 * 60
            for gridcell in [
                    x 
                    for x 
                    in dict_result.iterkeys() 
                    if x != 'timestamp_python' 
                    and x != 'timestamp_matlab'
                    ]:
                for wp in [
                        x 
                        for x 
                        in dict_result[gridcell]['generation'].iterkeys()]:
                    dict_cum_result[adm_level][wp] = {}
                    for key,value in {'availability': 'availability', 
                                      'Power_real':'energy_real', 
                                      'Power_100':'energy_100'}.iteritems(): 
                        tmp = [
                          [
                            x 
                            for x 
                            in [
                              dict_result[gridcell]['generation'][wp][key]
                            ]
                          ]
                        ]
                        if key == 'availability':
                            tmp_availability = [
                              np.average(
                                [
                                  sum(
                                    [
                                      x[i] 
                                      for 
                                      x in [
                                        item 
                                        for sublist 
                                        in tmp 
                                        for item
                                        in sublist
                                      ]
                                    ]
                                  ) 
                                  for i 
                                  in range(len(tmp[0][0]))
                                ][v:(v + int_target_interval_min / \
                                  int_source_interval_min)
                                ]
                              ) 
                              for v 
                              in range(0, len(tmp[0][0]), 
                                       int_target_interval_min / \
                                       int_source_interval_min
                              )
                            ]
                            if ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "original":
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_availability
                            elif ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "normalized":
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_availability / max(tmp_availability)
                        else:
                            tmp_energy = np.array(
                              [
                                np.sum(
                                  [
                                    sum(
                                      [
                                        x[i] 
                                        for x 
                                        in [
                                          item 
                                          for sublist
                                          in tmp 
                                          for item
                                          in sublist
                                        ]
                                      ]
                                    ) 
                                    for i 
                                    in range(len(tmp[0][0]))
                                  ][v:(v + int_target_interval_min / \
                                    int_source_interval_min)
                                  ]
                                ) 
                                for v 
                                in range(0, len(tmp[0][0]), 
                                         int_target_interval_min / \
                                         int_source_interval_min
                                )
                              ]
                            ) * int_source_interval_min / 60
                            tmp_power = [
                              np.average(
                                [
                                  sum(
                                    [
                                      x[i] 
                                      for x 
                                      in [
                                        item 
                                        for sublist
                                        in tmp 
                                        for item
                                        in sublist
                                      ]
                                    ]
                                  ) 
                                  for i 
                                  in range(len(tmp[0][0]))
                                ][v:(v + int_target_interval_min / \
                                  int_source_interval_min)
                                ]
                              ) 
                              for v 
                              in range(0, len(tmp[0][0]), 
                                       int_target_interval_min / \
                                       int_source_interval_min
                              )
                            ] 
                            if ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "original":
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_energy
                                dict_cum_result[adm_level][wp][key] = tmp_power
                            elif ctrl_dict_cumulative_results[
                                    'timeseries_format'] == "normalized":
                                p_rated = float(dict_result[gridcell][
                                  'generation'][wp]['p_nenn_total']) / 1000
                                dict_cum_result[adm_level][wp][value] = \
                                  tmp_energy / (p_rated * 24)
                                dict_cum_result[adm_level][wp][key] = \
                                  tmp_power / p_rated
            
        #calculate a single output value for the whole period
        elif ctrl_dict_cumulative_results['cumulation_level_time'] == "Period":
            int_target_interval_min = (
              dict_result['timestamp_python'][-1] - \
              dict_result['timestamp_python'][0]
            ).total_seconds() / 60
            for gridcell in [
                    x 
                    for x 
                    in dict_result.iterkeys() 
                    if x != 'timestamp_python' 
                    and x != 'timestamp_matlab'
                    ]:
                for wp in [
                        x 
                        for x 
                        in dict_result[gridcell]['generation'].iterkeys()]:
                    dict_cum_result[adm_level][wp] = {}
                    for key,value in {'availability': 'availability', 
                                      'Power_real':'energy_real', 
                                      'Power_100':'energy_100'}.iteritems():    
                        tmp = [
                          [
                            x 
                            for x 
                            in [
                              dict_result[gridcell]['generation'][wp][key]
                            ]
                          ]
                        ]
                        if key == 'availability':
                            dict_cum_result[adm_level][wp][value] = [
                              np.average(
                                [
                                  sum(
                                    [
                                      x[i] 
                                      for x 
                                      in [
                                        item 
                                        for sublist
                                        in tmp 
                                        for item
                                        in sublist
                                      ]
                                    ]
                                  ) 
                                  for i 
                                  in range(len(tmp[0][0]))
                                ]
                              )
                            ]
                        else:
                            tmp_energy = np.sum(
                              [
                                sum(
                                  [
                                    x[i] 
                                    for x 
                                    in [
                                      item
                                      for sublist
                                      in tmp 
                                      for item
                                      in sublist
                                    ]
                                  ]
                                ) 
                                for i 
                                in range(len(tmp[0][0]))
                              ]
                            ) * int_source_interval_min / 60
                            tmp_power = np.average(
                              [
                                sum(
                                  [
                                    x[i]
                                    for x
                                    in [
                                      item
                                      for sublist
                                      in tmp
                                      for item
                                      in sublist
                                    ]
                                  ]
                                ) 
                                for i 
                                in range(len(tmp[0][0]))
                              ]
                            )
                            dict_cum_result[adm_level][wp][value] = \
                              [tmp_energy]
                            dict_cum_result[adm_level][wp][key] = [tmp_power]
                    #add info about operation hours and utilized power curve to dict_cum_result
                    dict_cum_result[adm_level][wp][
                      'operation_hours'] = dict_result[gridcell][
                        'generation'][wp]['operation_hours']
                    dict_cum_result[adm_level][wp]['power_curve'] =\
                      dict_result[gridcell]['generation'][wp]['power_curve']
                    if 'full_load_hours' in i_result_postprocessing['method']:
                        dict_cum_result[adm_level][wp]['flh_factor'] = \
                          dict_result[gridcell]['generation'][wp]['flh_factor']
            
    Info("Cummulative results for selected boundary successfully calculated.", 
         1, dict_console_info)
                
    return arr_error_calccum, dict_cum_result