#!/bin/python

import pandas as pd
import numpy as np
import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup

def query_website(dateRange,magRange,boxRange,depthRange):
    
    '''
    dateRange: start date and end date in 'YYYY-MM-DD' format as list; [startDate,endDate]
    magRange: minimum and maximum moment magnitude as list; [minMag,maxMag]
    boxRange: lower left corner and upper right corner coordinates as list; [lonMin,lonMax,latMin,latMax]
    depthRange: minimum and maximum depth in kilometers as list; [minDepth,maxDepth]
    '''
    
    startYr = int(dateRange[0].split('-')[0])
    startMo = int(dateRange[0].split('-')[1])
    startDy = int(dateRange[0].split('-')[2])
    
    endYr = int(dateRange[1].split('-')[0])
    endMo = int(dateRange[1].split('-')[1])
    endDy = int(dateRange[1].split('-')[2])
    
    minMag = magRange[0]
    maxMag = magRange[1]

    llon = boxRange[0]
    ulon = boxRange[1]
    llat = boxRange[2]
    ulat = boxRange[3]
    
    minDepth = depthRange[0]
    maxDepth = depthRange[1]
    
    beginning_of_link = 'https://www.globalcmt.org/cgi-bin/globalcmt-cgi-bin/CMT5/form?itype=ymd&'
    middle_of_link1 = 'yr=%4.0f&mo=%.02f&day=%02.0f&otype=ymd&oyr=%04.0f&omo=%02.0f&oday=%02.0f' % (startYr,startMo,startDy,endYr,endMo,endDy)
    middle_of_link2 = '&jyr=1976&jday=1&ojyr=1976&ojday=1&nday=1&'
    middle_of_link3 = 'lmw=%.1f&umw=%.1f&llat=%.4f&ulat=%.4f&llon=%.4f&ulon=%.4f&lhd=%.0f&uhd=%.0f&' % (minMag,maxMag,llat,ulat,llon,ulon,minDepth,maxDepth)
    end_of_link = 'lts=-9999&uts=9999&lpe1=0&upe1=90&lpe2=0&upe2=90&list=0'
    
    link = beginning_of_link + middle_of_link1 + middle_of_link2 + middle_of_link3 + end_of_link
    
    return link

def get_html_data(link):
    
    try:
        session = HTMLSession()
        response = session.get(link)
        html = response.content
        return html
	 
    except requests.exceptions.RequestException as e:
        print(e)

def parse_html(html):

    soup = BeautifulSoup(html,'html.parser')
    
    return soup

def get_parameters(soup):
    
    '''
    returns timestamp, longitude, latitude, depth, moment magnitude, scalar moment, and fault plane solutions
    '''
    
    timestamp = []
    Lon = []
    Lat = []
    Dep = []
    Mw = []
    M0 = []
    faultPlanes = []
    for line in soup.get_text().split('\n'):  
        #print(line)
        if 'Date' in line:
            timestamp.append('%4.0f-%02.0f-%02.0f %02.0f:%02.0f:%03.1f' % (float(line[7:12])
                                                                   ,float(line[13:15])
                                                                   ,float(line[16:18])
                                                                   ,float(line[36:38])
                                                                   ,float(line[39:41])
                                                                   ,float(line[42:46])))
        if 'Mw =' in line:
            Mw.append(float(line[6:10]))
            M0.append(float(line.split('=')[-1]))

        if 'Fault plane:' in line:
            strike = int(line.split('=')[1].split(' ')[0])
            dip = int(line.split('=')[2].split(' ')[0])
            rake = int(line.split('=')[3])
            faultPlanes.append([strike,dip,rake])
            
        if 'Lat' in line:
            Lat.append(float(line.split(' ')[3]))
            Lon.append(float(line.split(' ')[-1]))
            
        if 'Depth' in line:
            Dep.append(float(line.split('Depth=')[1][:5]))
            
    result = []
    for i, t in enumerate(timestamp):

        m1 = Mw[i]
        m2 = M0[i]
        lon = Lon[i]
        lat = Lat[i]
        dep = Dep[i]
        faultPlane1 = faultPlanes[2*i]
        faultPlane2 = faultPlanes[2*i+1]

        result.append([t,lon,lat,dep,m1,m2,faultPlane1,faultPlane2])

    df = pd.DataFrame(result,columns=['timestamp','longitude','latitude','depth','Mw','M0','faultPlane1','faultPlane2'])
    
    return df

def more_solutions(soup):
    
    for line in soup.get_text().split('\n'):
        if 'More solutions' in line: 
            flag = 1
            break
        else:
            flag = 0
    if flag:
        return str(soup.find_all('h2')[-1]).split('\"')[1].replace('amp;','')
    else:
        return(0)
    
def save_file(df,dateRange):
    
    file = 'Harvard_CMT_%s_%s.csv' % (dateRange[0],dateRange[1])
    df.to_csv(file,sep=',',header=True,index=False,index_label=None)
    
    
def get_events(dateRange,magRange,boxRange,depthRange):

    '''
    dateRange: start date and end date in 'YYYY-MM-DD' format as list; [startDate,endDate]
    magRange: minimum and maximum moment magnitude as list; [minMag,maxMag]
    boxRange: lower left corner and upper right corner coordinates as list; [lonMin,lonMax,latMin,latMax]
    depthRange: minimum and maximum depth in kilometers as list; [minDepth,maxDepth]
    '''

    frames = []
    
    link = query_website(dateRange,magRange,boxRange,depthRange)
#    print(link)
    while isinstance(link,str):
		        
        # parse the html data and get the event information
        file = get_html_data(link)
        soup = parse_html(file)
        frames.append(get_parameters(soup))
        
        # check if there are more events to grab
        # if so, continue
        link = more_solutions(soup)
        
    # merge the frames into a single dataframe
    df = pd.concat(frames).reset_index(drop=True)
    
    # save the data
    save_file(df,dateRange)
        
    return df
