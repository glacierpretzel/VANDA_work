#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  1 18:48:04 2026
The code will output a mseed file with the response attached and a prefilter applied 
@author: kitsellusted
"""

from obspy import *
# import matplotlib.pyplot as plt
# import json
# from obspy.clients.nrl import NRL
import numpy as np
import sys


# Read in Dry valley deployment miniseed files
st=read('fryxell_deployment.mseed') 
fr = st.copy()
fr.filter('bandpass', freqmin=1, freqmax=10)
start = UTCDateTime('2025-11-21T09:31:00')
end = UTCDateTime('2025-11-21T09:32:00')

fr.slice(starttime=start, endtime=end)

for tr in fr.slice(starttime=start, endtime=end):
    idx = np.argmax(np.abs(tr.data))
    max_time = tr.times("utcdatetime")[idx]
    max_val = tr.data[idx]
    print(tr.stats.channel, tr.data.max(), max_time)

# st=st.copy()

#Remove the 0 value streams from the 2017 deployment


#Trimminging to the Fryxell deployment timeline


