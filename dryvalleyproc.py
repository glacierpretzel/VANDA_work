#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 18:48:04 2026
The code will output a mseed file with the response attached and a prefilter applied 
@author: kitsellusted
"""

from obspy import read, read_inventory, UTCDateTime
# import matplotlib.pyplot as plt
# import json
# from obspy.clients.nrl import NRL
import sys


# Read in Dry valley deployment miniseed files
st=read('/Users/kitsellusted/Desktop/Dry_valley_data/*.mseed') 


# st=st.copy()

#Remove the 0 value streams from the 2017 deployment
for tr in st:  
    if len(tr)<=0:
        st.remove(tr)


#Trimminging to the Fryxell deployment timeline
fryxell = st.trim(UTCDateTime("2025-11-21T01:00:00.000000Z"), 
                  UTCDateTime('2025-11-26T04:13:10.220000Z'))  
fryxell.merge()
#Changing the station name to match the inventory object
fryxell[0].stats.station = 'DV01' 
fryxell[1].stats.station = 'DV01'
fryxell[2].stats.station = 'DV01'
fryxell.remove(fryxell[-1]) #Get rid of the BKO channel
# print(fryxell)

inv=read_inventory('/Users/kitsellusted/grad_school/VANDA_work/polaris_md/polaris.xml')

# Attach Responsefor Dry Valley set-up
# Digi= Guralp Minimus Plus, Sensor = Nanometrics TCH120
print('attaching response')
fryxell.attach_response(inv) 
# Decon
sr = fryxell[0].stats.sampling_rate
pre_filt = [0.001, 0.005, sr / 2 - 2, sr / 2]
print('removing response')
fryxell.remove_response(pre_filt=pre_filt, output="DISP")
fryxell.detrend(type="linear") #removes upward/dwonward slope from data
fryxell.detrend(type="demean") #centers the data around 0

# st.plot()







# #filter
# st.filter('bandpass', freqmin=1, freqmax=2)

# #
# # st.plot()
# start=UTCDateTime("2025-11-21T00:33:21.000000Z")
# end=UTCDateTime('2025-11-21T23:45:54.920000Z ')
# st_data=st.slice(starttime=start,endtime=end)
# # print("bandpass between [1,5 Hz]")
# st_data.plot(title='what is that')
# plt.show()

# # st_data.plot()

fryxell.write("fryxell_deployment.mseed", format="MSEED", encoding="float32")
sys.exit()


