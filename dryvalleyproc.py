#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 18:48:04 2026

@author: kitsellusted
"""

from obspy import read, read_inventory, UTCDateTime
import matplotlib.pyplot as plt
import json
from obspy.clients.nrl import NRL
# nrl = NRL()

st=read('/Users/kitsellusted/Desktop/*.mseed') #startign with just one trace

st=st.copy()

#Remove the 0 value streams from the 2017 deployment
for tr in st:  
    if len(tr)<=0:
        st.remove(tr)
st=st.merge()
# Attach Responsefor Dry Valley set-up
# Digi= Guralp Minimus Plus, Sensor = Nanometrics TCH120
   
inv=read_inventory('/Users/kitsellusted/grad_school/VANDA/polaris_md/polaris.xml')
print(inv[0])
st.attach_response(inv) #Something doesn't match
st.remove_response(inv, output="DISP") #this gives an error
#REMOVE RESPONSE



st.detrend(type="linear") #removes upward/dwonward slope from data
st.detrend(type="demean") #centers the data around 0


#filter
st.filter('bandpass', freqmin=1, freqmax=2)

#
# st.plot()
start=UTCDateTime("2025-11-21T00:33:21.000000Z")
end=UTCDateTime('2025-11-21T23:45:54.920000Z ')
st_data=st.slice(starttime=start,endtime=end)
# print("bandpass between [1,5 Hz]")
st_data.plot(title='what is that')
plt.show()

# st_data.plot()


