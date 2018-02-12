#!/bin/python

import pandas as pd
import numpy as np
import time
from datetime import datetime
import calendar

'''
Reads and modifies 4 catalog types:
Advanced National Seismic System (ANSS)
Southern California Earthquake Data Center (SCEDC)
International Seismological Centre (ISC)/Incorporated Research Institutes for Seismology (IRIS)
GEONET


'''

def datetime_split(df,separator='/'):
    
    '''
    
    Splits datetime object into year, month, day, hour, minute, second for computation of epoch time and year fraction.
    Corrects the datetime for the GEONET catalog (i.e. removes the 'Z')
    
    If the datetime object has a separator other than '/', it must defined.
    
    Input: dataframe df with 'DateTime' column where Date and Time are separated by a space and separator (optional)
    Returns: the original dataframe with year, month, day, hour, minute, second columns adde
    
    '''

    # separate date and time
    dateTimeStamp = list(df['DateTime'])
    dateTimeSplit = [x.split(' ') for x in dateTimeStamp]

    Dates = [x[0] for x in dateTimeSplit]
    Times = [x[1] for x in dateTimeSplit]

    # separate date to yr, mo, dy
    dateSplit = [x.split(separator) for x in Dates]

    years = [x[0] for x in dateSplit]
    months = [x[1] for x in dateSplit]
    days = [x[2] for x in dateSplit]

    # separate time to hr, mi, sc
    timeSplit = [x.split(':') for x in Times]

    hours = [x[0] for x in timeSplit]
    minutes = [x[1] for x in timeSplit]
    seconds = [x[2] for x in timeSplit]
    
    
    if 'Z' in seconds[0]: # GEONET
        secondsSplit = [x.split('Z') for x in seconds]
        seconds = [x[0] for x in secondsSplit]
        dateTime = ['%.0f-%02.0f-%02.0f %02.0f:%02.0f:%6.3f' % (float(a),float(b),float(c),float(d),float(e),float(f)) for a, b, c, d, e, f in zip(years,months,days,hours,minutes,seconds)]
        df['DateTime'] = pd.Series(dateTime)

    df['year'] = pd.Series(years)
    df['month'] = pd.Series(months)
    df['day'] = pd.Series(days)
    df['hour'] = pd.Series(hours)
    df['minute'] = pd.Series(minutes)
    df['second'] = pd.Series(seconds)
    
    return df

def compute_epoch(df):
    
    '''
    Computes epoch time and year fraction for year, month, day, hour, minute, second in dataframe df.
    Sorts the dataframe based on Epoch time in ascending order.
    
    Input: dataframe df must have year, month, day, hour, minute, second columns
    
    Returns: original dataframe with Epoch and YearFrac columns
    '''
    
    pattern = '%Y %m %d %H %M %S'
    date_time = df.apply(lambda x: '%.0f %.0f %.0f %.0f %.0f %.0f'
                          % (float(x['year']),float(x['month']),float(x['day']),float(x['hour']),float(x['minute']),float(x['second'])),axis=1)
    
    epoch = [int(calendar.timegm(time.strptime(date_time[x],pattern)))
         for x in np.arange(0,len(date_time),1)]

    df['Epoch'] = pd.Series(epoch,index=df.index)
    df = df.sort_values(['Epoch'],ascending=1)
    df = df.reset_index(drop=True)
    
    # compute year fraction and add to the dataframe
    yearFractions = [1970 + (x)/(24*3600*365.25) for x in df.Epoch]
    df['YearFrac'] = pd.Series(yearFractions,index=df.index)
    
    return df

def mod_SCEDC_csv(fileName):
    
    '''
    Reads and modifies a Southern California Earthquake Data Center (SCEDC) catalog that has a white space delimiter.
    The columns may have been renamed to make column headers consistent among all catalog modifiers.
    
    Input: name of input file
    
    Returns: dataframe with all the original columns except for 'Date' and 'Time' which are merged into 'DateTime'. 
    Also columns 'Epoch' and 'YearFrac' are added.
    
    '''
    
    df = pd.read_csv(fileName,delim_whitespace=True)
    df.columns = ['Date','Time','EventType','GT','Magnitude','MagType','Latitude','Longitude','Depth','Quality','EventID','NumPhases','NumGroundMotion']
    
    df['DateTime'] = pd.Series(['%s %s' % (x,y) for x,y in zip(df.Date,df.Time)])
    df = datetime_split(df)
    df = compute_epoch(df)
    
    df = df[['DateTime','YearFrac','Epoch','Longitude','Latitude','Depth','Magnitude','MagType','Quality','EventType','GT','EventID','NumPhases','NumGroundMotion']]
    
    return df

def mod_ANSS_csv(fileName):
    
    '''
    Reads and modifies an Advanced National Seismic system (ANSS) CSV-formatted catalog that has a ',' delimiter.
    The columns may have been renamed to make column headers consistent among all catalog modifiers.
    
    Input: name of input file
    
    Returns: dataframe with all the original columns with additional columns 'Epoch' and 'YearFrac'.
    
    '''

    df = pd.read_csv(fileName,sep=',',header=0)
    
    df = datetime_split(df)
    df = compute_epoch(df)
    
    df = df[['DateTime','YearFrac','Epoch','Longitude','Latitude','Depth','Magnitude','MagType','NbStations', 'Gap', 'Distance', 'RMS', 'Source', 'EventID']]

    return df

def mod_IRIS_csv(fileName):

    '''
    Reads and modifies an Incorporated Research Institutes for Seismology (IRIS) catalog that has a '|' delimiter.
    This catalog is a mirror of the International Seismological Centre (ISC) catalog and should therefore be exactly the same.  
    The columns may have been renamed to make column headers consistent among all catalog modifiers.
    
    Input: name of input file
    
    Returns: dataframe with all the original columns with additional columns 'Epoch' and 'YearFrac'.
    
    '''
    
    df = pd.read_csv(fileName,sep='|',header=0)
    
    # reformat date and time
    dateTimeStamp = list(df[' Time '])
    dateTimeSplit = [x.split('T') for x in dateTimeStamp]
    df['DateTime'] = pd.Series(['%s %s' % (x[0],x[1]) for x in dateTimeSplit])
    
    df = datetime_split(df,separator='-')
    df = compute_epoch(df)
    
    df.columns = ['EventID','Time','Latitude','Longitude','Depth','Author','Catalog','Contributor','ContributorID'
                 ,'MagType','Magnitude','MagAuthor','EventLocationName','DateTime','year','month','day','hour'
                 ,'minute','second','Epoch','YearFrac']

    df = df[['DateTime','YearFrac','Epoch','Longitude','Latitude','Depth','Magnitude','MagType'
            ,'EventID','Author','Catalog','Contributor','ContributorID','MagAuthor','EventLocationName']]
    
    return df

def mod_GEONET_csv(fileName):
    
    '''
    Reads and modifies a GEONET catalog that has a ',' delimiter.
    The columns may have been renamed to make column headers consistent among all catalog modifiers.
    
    Input: name of input file
    
    Returns: dataframe with all the original columns with additional columns 'Epoch' and 'YearFrac'.
    
    '''
    
    df = pd.read_csv(fileName,sep=',',header=0)
    
    # reformat date and time
    dateTimeStamp = list(df['origintime'])
    dateTimeSplit = [x.split('T') for x in dateTimeStamp]
    df['DateTime'] = pd.Series(['%s %s' % (x[0],x[1]) for x in dateTimeSplit])
    
    df = datetime_split(df,separator='-')
    df = compute_epoch(df)
    
    df.columns = ['PublicID','EventType','OriginTime','ModificationTime','Longitude','Latitude','Magnitude'
                 ,'Depth','MagType','DepthType','EvaluationMethod','EvaluationStatus','EvaluationMode'
                 ,'EarthModel','UsedPhaseCount','UsedStationCount','MagnitudeStationCount','MinimumDistance'
                 ,'AzimuthalGap','OriginError','MagnitudeUncertainty','DateTime','year','month','day','hour'
                 ,'minute','second','Epoch','YearFrac']
    
    df = df[['DateTime','YearFrac','Epoch','Longitude','Latitude','Depth','Magnitude','MagType'
            ,'PublicID','EventType','ModificationTime','DepthType','EvaluationMethod','EvaluationStatus','EvaluationMode'
            ,'EarthModel','UsedPhaseCount','UsedStationCount','MagnitudeStationCount','MinimumDistance'
            ,'AzimuthalGap','OriginError','MagnitudeUncertainty']]
    
    return df
