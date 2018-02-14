#!/bin/python

'''


'''

def get_transect_coords(center,azimuth,length,width,ellipsoid='clrk66'):
    
    '''
    Computes endpoints of 2 perpendicular transects.
    
    Input:
    center = center point (lon,lat)
    azimuth = azimuth to transect from north in degrees
    length = distances in meters from center point along transect (lengthMin,lengthMax)
    width = distances in meters perpendicular to transect (widthMin,widthMax)
    ellipsoid = ellipsoid to use for the projection (optional, auto-set to clrk66)
    
    Returns:
    g = projection (for project_points() function)
    parallel transect coords (for map plotting)
    perpendicular transect coords (for map plotting)
    
    '''

    from pyproj import Geod
    
    # define the projection
    g = Geod(ellps=ellipsoid) 
    
    # parallel
    endlon1, endlat1, backaz1 = g.fwd(center[0],center[1],azimuth,length[0])
    endlon2, endlat2, backaz2 = g.fwd(center[0],center[1],azimuth,length[1])
    
    parallel = [[endlon1,endlon2],[endlat1,endlat2]]
    
    # perpendicular
    endlon1, endlat1, backaz1 = g.fwd(center[0],center[1],azimuth-90,width[0])
    endlon2, endlat2, backaz2 = g.fwd(center[0],center[1],azimuth-90,width[1])
    
    perpendicular = [[endlon1,endlon2],[endlat1,endlat2]]
    
    return(g, parallel, perpendicular)

def project_points(df,g,center,azimuth):
    
    '''
    Projects all points onto the transect defined by 
    center point (center) and azimuth (azimuth) in projection (g).
        
    Input: 
    df = pandas dataframe with at least "Longitude" and "Latitude" columns.
    g = projection (given by get_transect_coords(center,azimuth,length,width)) or you could set it yourself
    center = center point (lon,lat)
    azimuth = azimuth to transect from north in degrees
    
    Returns:
    df with added columns 'xx' and 'yy' where
    xx is distance in kilometers from center point along transect
    yy is distance in kilometers from center point along the perpendicular transect
    
    '''

    import pandas as pd
    import numpy as np
    
    deg2rad = np.pi/180.0
    
    xx = []
    yy = []
    for lo, la in zip(df.Longitude,df.Latitude):

        az, baz, length = g.inv(center[0],center[1],lo,la)

        length = length/1e3 # convert to km

        xx.append(length*np.cos((azimuth-az)*deg2rad))
        yy.append(length*np.sin((azimuth-az)*deg2rad))

    proj = pd.DataFrame({'xx':xx,'yy':yy},index=df.index)
    df = pd.concat([df,proj],axis=1)
    
    return df
