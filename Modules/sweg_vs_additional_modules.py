#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
SWEG VS
Additional small Modules

'''
def loadmat(filename):
    '''
    this function should be called instead of direct spio.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects
    source: http://stackoverflow.com/questions/7008608/scipy-io-loadmat-nested-structures-i-e-dictionaries
    '''
    import scipy.io as spio    
    
    data = spio.loadmat(
      filename, struct_as_record=False, squeeze_me=True, chars_as_strings=True)
    return _check_keys(data)

def _check_keys(dict):
    '''
    checks if entries in dictionary are mat-objects. If yes
    todict is called to change them to nested dictionaries
    source: http://stackoverflow.com/questions/7008608/scipy-io-loadmat-nested-structures-i-e-dictionaries
    '''
    
    import scipy.io as spio
    
    for key in dict:
        if isinstance(dict[key], spio.matlab.mio5_params.mat_struct):
            dict[key] = _todict(dict[key])
    return dict        

def _todict(matobj):
    '''
    A recursive function which constructs from matobjects nested dictionaries
    source: http://stackoverflow.com/questions/7008608/scipy-io-loadmat-nested-structures-i-e-dictionaries
    '''
    import scipy.io as spio
    
    dict = {}
    for strg in matobj._fieldnames:
        elem = matobj.__dict__[strg]
        if isinstance(elem, spio.matlab.mio5_params.mat_struct):
            dict[strg] = _todict(elem)
        else:
            dict[strg] = elem
    return dict
    
def matnum2datetime(matlab_datenum):
    '''
    Function converting the Matlab date format to Python datetime object
    Source: http://sociograph.blogspot.de/2011/04/how-to-avoid-gotcha-when-converting.html
    '''
    from datetime import datetime, timedelta
    
    if matlab_datenum != 0:
        day_frac = round(matlab_datenum%1 * 24,0) / 24
        python_datetime = (datetime.fromordinal(int(matlab_datenum)) + \
          timedelta(days=day_frac) - \
          timedelta(days = 366)).replace(microsecond=0)
    else:
        python_datetime = None
    
    return python_datetime
    
def create_timestamp_year(year, interval):
    '''
    Creates array of timestamps for a given year and interval.
    '''
    from datetime import datetime, timedelta
    
    start_year = datetime(year,1,1,0,0)
    end_year = datetime(year,12,31,23,0)
    interval = timedelta(seconds=interval * 60)
    arr_timestamps_year = [
      start_year + i * interval 
      for i 
      in range(int(
        (end_year-start_year).total_seconds()/interval.total_seconds()) + 1)
    ]
    
    return arr_timestamps_year
     

def convert_date(str_date_format, str_input):
    '''
    Converts string representation of date to datetype object.
    
    Keyword arguments:
    
    str_date_format -- String of the structure of the date, eg "ddmmyyyy" or "dd.mm.yyyy"
    str_input -- String containing the values in the format specified by str_date_format
    
    Output:
    date_output -- datetime object datetime.date(year, month, day)
    '''
    
    import datetime
    
    if str_input != "0":
        #identify date structure from str_date_format
        int_day_pos_l = str_date_format.index('d')
        int_month_pos_l = str_date_format.index('m')
        int_year_pos_l = str_date_format.index('y')
        int_day_pos_r = str_date_format[::-1].index('d')
        int_month_pos_r = str_date_format[::-1].index('m')
        int_year_pos_r = str_date_format[::-1].index('y')
        int_len_date = len(str_date_format)   
        #apply date structure to str_input
        year = int(str_input[int_year_pos_l:int_len_date-int_year_pos_r])
        month = str_input[int_month_pos_l:int_len_date-int_month_pos_r]
        day = str_input[int_day_pos_l:int_len_date-int_day_pos_r]
        
        if day == '':
            day = 1
        if month == '':
            month = 7
        
        date_output = datetime.date(year, int(month), int(day))
    else:
        #date = None, if no date exists
        date_output = None
    return date_output
    
def console_info(str_output,int_console_detail, dict_console_info):
    '''
    Writes formatted output to the console window.
    
    Keyword arguments:
        
    str_output -- str containing the information to be displayed on the console
        
    int_console_detail -- int 1 = main info, 2 = intermediate steps, 3 = intermediate values
        
    dict_console_info -- dictionary {'time_start': time_start, 
      'ctrl_bol_console_output': ctrl_dict_console_output['bol_console_output'], 
      'ctrl_int_console_details': ctrl_dict_console_output['int_console_details']}

    '''
    import datetime   
    
    if dict_console_info['ctrl_bol_console_output'] == 1:
        if int_console_detail <= dict_console_info['ctrl_int_console_details']:
            if int_console_detail == 3:
                print "> " + str_output.rstrip()
            else:
                print '{0:74}{1:4.5f}'.format(
                  str_output.rstrip(),
                  (datetime.datetime.now() - \
                  dict_console_info['time_start']).total_seconds()
                )
                
                
def plot_values(arr_plot_info, str_header=""):
    '''
    Creates plot of supplied data.
    '''
    import numpy as np
    from matplotlib.dates import DayLocator, HourLocator, DateFormatter
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    fig = plt.figure(figsize=(20,10), dpi = 100)
    

    for plot in arr_plot_info:
        ax = plt.subplot(plot['subplot'])
        
        x = plot['x_vals'][:14*24] 
        y = plot['y_vals'][:14*24]  
        
        if plot['plottype'] == "line":
            ax.plot(x, y, '-', color=plot['color'])
        elif plot['plottype'] == "bar":
            
            width = 1 / len(x) - 0.03
            ax.bar(x, y, color=plot['color'], width = width)
            #ax.bar(x, y, color=plot['color'])
        elif plot['plottype'] == "point":
            ax.plot(x, y, 'o', color=plot['color'])
        elif plot['plottype'] == "linepoint":
            ax.plot(x, y, 'o-', color=plot['color'])
            
        if plot['x_date'] == True:
            ax.xaxis_date()
            if len(x) >= 96:
                ax.xaxis.set_major_locator( DayLocator(interval=1))
            else:
                ax.xaxis.set_major_locator( HourLocator(np.arange(0,24,6)) )
            ax.xaxis.set_major_formatter( DateFormatter('%Y-%m-%d %H:%M:%S') )
            ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
            fig.autofmt_xdate()
        
        ax.grid(True)
        
        ax.set_xlabel(plot['x_label'])
        ax.set_ylabel(plot['y_label'])
        ax.yaxis.set_label_coords(-0.1, 0.5)
        ax.set_title(plot['title'])
        if plot['y_range'] != []:
            ax.set_autoscaley_on(False)
            if len(plot['y_range']) == 2:
                ax.set_ylim(
                  bottom=float(plot['y_range'][0]), 
                  top=float(plot['y_range'][1])
                )
            elif len(plot['y_range']) == 1:
                ax.set_ylim(bottom=float(plot['y_range'][0]))
        fontP = FontProperties()
        fontP.set_size('small')
        #box = ax.get_position()
        #ax.set_position([box.x0, box.y0, box.width * 0.75, box.height])
    fig.suptitle(str_header, fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    plt.show()
    
def drop_column_in_db_table(schema, table_name, col_name, cur, conn):
    '''
    Drops a single column.

    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    col_name -- string containing column name
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection

    '''
    str_sql_statement = "ALTER table " + schema + "." + table_name + \
                        " DROP COLUMN IF EXISTS " + col_name
    cur.execute(str_sql_statement)
    conn.commit()
    return


def add_column_2_db_table(schema, table_name, col_name, data_type, cur, conn):
    '''
    Adds a column to an existing table.

    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    col_name -- string containing column name
    data_type -- string containing data type of column
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    str_sql_statement = "ALTER table " + schema + "." + table_name + \
                        " ADD COLUMN " + col_name + " " + data_type
    #print str_sql_statement
    cur.execute(str_sql_statement)
    conn.commit()
    return


def update_row(
        schema, table_name, arr_col_name, arr_value, col_cond, 
        arr_value_cond, cur, conn):
    '''
    Updates a value in a column for the given condition.

    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    arr_col_name -- array containing column name(s) to be updated
    arr_value -- array containing update values
    col_cond -- string containing column name of conditional column
    arr_value_cond -- array containing conditional values
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection

    '''
    str_sql_statement = ""
    #start = datetime.now()
    if len(arr_value[0]) == len(arr_value_cond):
        #prepare sql_statement for update if column_update==True
    
        for row in range(len(arr_value[0])):
            #for update of multiple rows in one column
            if len(arr_col_name) == 1:
                if isinstance(arr_value[0][row], list) == True:
                    str_sql_statement += "UPDATE " + schema + "." + table_name + \
                  " SET " + arr_col_name[0] + " = Array" + \
                  str(arr_value[0][row]) + \
                  " WHERE " + col_cond + " = '" + \
                  str(arr_value_cond[row]) + "';"
                else:
                    str_sql_statement += "UPDATE " + schema + "." + table_name + \
                      " SET " + arr_col_name[0] + " = '" + \
                      str(arr_value[0][row]) + \
                      "' WHERE " + col_cond + " = '" + \
                      str(arr_value_cond[row]) + "';"
            else:
                #for update of multiple rows in multiple columns
                str_sql_statement += "UPDATE " + schema + "." + table_name + \
                  " SET "
                for int_column in range(len(arr_col_name)):
                    if isinstance(arr_value[int_column][row],list) == True:
                        str_sql_statement += arr_col_name[int_column] + \
                          " = Array" + str(arr_value[int_column][row]) + ", "   
                    else:
                        str_sql_statement += arr_col_name[int_column] + \
                        " = '" + str(arr_value[int_column][row]) + "', " 
                str_sql_statement = str_sql_statement[:-2] + \
                  " WHERE " + col_cond + " = '" + \
                  str(arr_value_cond[row]) + "';"
        cur.execute(str_sql_statement)
        conn.commit()
    return


def create_db_table(
        schema, table_name, arr_cols, arr_col_dtype, str_id, cur, conn):
    '''
    Creates a table with the columns specified in colname_data_type.

    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    arr_cols -- array containing column names
    arr_col_dtype -- array containing datatypes of columns
    str_id -- string containing column name of primary key column
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    str_sql_statement = "CREATE TABLE IF NOT EXISTS " + \
      schema + "." + table_name + "("
    for col_name in arr_cols:
        str_sql_statement += col_name + " " + \
          arr_col_dtype[arr_cols.index(col_name)] + ", "
    str_sql_statement += "CONSTRAINT " + table_name + \
      "_pk PRIMARY KEY (" + str_id + "));"
    cur.execute(str_sql_statement)
    conn.commit()
    return


def insert_data_into_db_table(
        schema, table_name, arr_dict_columns_info, arr_insert_data, cur, conn):
    '''
    Inserts one or several rows at once into database table.

    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    arr_dict_columns_info -- array of dicts containing info on target table
    arr_insert_data -- array containing data to be inserted
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection

    '''
    str_insert_columns = ""
    str_insert_placeholder = ""
    for int_column in range(len(arr_dict_columns_info)):
        if arr_dict_columns_info[int_column] != arr_dict_columns_info[-1]:
            str_insert_columns += arr_dict_columns_info[
              int_column]['column_name'] + ", "
            str_insert_placeholder += "%s,"
        else:
            str_insert_columns += arr_dict_columns_info[
              int_column]['column_name']
            str_insert_placeholder += "%s" 
    str_sql_statement = "INSERT INTO "  + schema + "." + table_name + \
      " (" + str_insert_columns + ") VALUES " 
    args_str = ','.join(cur.mogrify(
      "(" + str_insert_placeholder + ")", x) for x in arr_insert_data
    )
    cur.execute(str_sql_statement + args_str)
    conn.commit()
    return


def drop_db_table(schema, table_name, cur, conn):
    '''
    Drops table from database.
    
    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    str_sql_statement = "DROP TABLE " + schema + "." + table_name
    cur.execute(str_sql_statement)
    conn.commit()
    return
    
def retrieve_from_db_table(schema, table_name, arr_col_name, cur):
    '''
    Retrieves data from database table.

    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    arr_col_name -- array containing column names whose data is to be retrieved
    cur -- handle of psycopg cursor
    '''
    str_sql_statement = "SELECT " + [str(x) for x in arr_col_name][0] + \
      " FROM " + schema + "." + table_name
    cur.execute(str_sql_statement)
    data = [row[0] for row in cur.fetchall()]
    return data
    
    
def insert_data_db_2(
        schema, table_name, arr_dict_columns_info, arr_insert_data, cur, conn):
    '''
    Inserts only data to db table that does not yet exists.
    
    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    arr_dict_columns_info -- array of dicts containing info on target table
    arr_insert_data -- array containing data to be inserted
    arr_col_name -- array containing column names whose data is to be retrieved
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    #get all values of the specified columns
    col_name = [column['column_name'] for column in arr_dict_columns_info]
    #retrieve data from table
    arr_retrieve = retrieve_from_db_table(schema, table_name, col_name, cur)
    if arr_retrieve == []:
        insert_data_into_db_table(
          schema, table_name, arr_dict_columns_info, arr_insert_data, 
          cur, conn
        )
    else:
        arr_insert_data = [x for x in arr_insert_data 
          if x[0] not in arr_retrieve
        ]
        if arr_insert_data != []:
            insert_data_into_db_table(
              schema, table_name, arr_dict_columns_info, arr_insert_data, 
              cur, conn
            )
            
def retrieve_comment_from_column(schema, table_name, col_name, cur, conn):
    '''
    Retrieve comment from specific column in database table.
    
    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    col_name -- string containing column name
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    str_sql_statement = """SELECT pgd.description 
    FROM pg_catalog.pg_statio_all_tables as st 
    inner join pg_catalog.pg_description pgd on (pgd.objoid=st.relid)
    inner join information_schema.columns c on (pgd.objsubid=c.ordinal_position
    and  c.table_schema=st.schemaname and c.table_name=st.relname)
    WHERE  c.table_schema='""" + schema + """' and c.table_name='""" + \
    table_name + """' and c.column_name = '""" + \
    col_name.replace('"', '') + """' GROUP BY c.table_schema, c.table_name, 
    c.column_name, pgd.description;"""
    cur.execute(str_sql_statement)
    str_comment_retrieved = [row[0] for row in cur.fetchall()]
    return str_comment_retrieved
            
def add_comment2column(schema, table_name, col_name, str_comment, cur, conn):
    '''
    Add comment to specific column in database table.
    
    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    col_name -- string containing column name
    str_comment -- string containing text for comment
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    str_sql_statement = "COMMENT ON COLUMN " + schema + "." + table_name + \
      "." + col_name + " IS '" + str_comment + "';"
    cur.execute(str_sql_statement)
    conn.commit()
    return
    
def delete_row(schema, table_name, col_cond, value_cond, cur, conn):
    '''
    Deletes row from given database table.
    
    Keyword arguments:
    schema -- string containing name of database schema
    table_name -- string containing table name
    col_cond -- string containing column name that contains condition
    value_cond -- conditional value 
    cur -- handle of psycopg cursor
    conn -- handle of psycopg connection
    '''
    str_sql_statement = "DELETE FROM " + schema + "." + table_name + \
      " WHERE " + col_cond + " = " + value_cond * ";"
    cur.execute(str_sql_statement)
    conn.commit()
    return