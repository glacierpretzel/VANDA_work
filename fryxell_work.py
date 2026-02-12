#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 30 22:45:41 2026

@author: kitsellusted
"""
from obspy import *
from obspy.clients.fdsn import Client
import matplotlib.pyplot as plt
import sys
from obspy import *
from obspy.signal.trigger import classic_sta_lta, trigger_onset
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
import matplotlib.dates as mdates
import argparse
from obspy.taup import TauPyModel
from obspy.geodetics.base import gps2dist_azimuth
from obspy.geodetics.base import kilometer2degrees

#DEFINITIONS--------------------------------------------------

def create_parser():
    parser = argparse.ArgumentParser(description="Use Obspy to plot waveforms.")
    parser.add_argument(
        "date1",
        action="store",
        type=str,
        help="Generate plot starting at this time [YYYY-MM-DDTHH:MM:SS]",
    )
    parser.add_argument(
        "date2",
        action="store",
        type=str,
        help="Generate plot starting at this time [YYYY-MM-DDTHH:MM:SS]",
    )

    return parser
#--------------------------------------------------------------------------
args = create_parser().parse_args()

date1 = UTCDateTime(args.date1)
date2 = UTCDateTime(args.date2)
client2 = Client('IRIS')

try:
    st = client2.get_waveforms(
        station='VNDA',
        network='*',
        location='*',
        channel='BH*',
        starttime=date1,
        endtime=date2,
        attach_response = True
    )
except:
    print("Unable to get data!")
    sys.exit()

# Preprocessing
st.merge(fill_value = 'interpolate')

#REMOVE RESPONSE

st.remove_response(output="DISP")
st.detrend(type="linear") #removes upward/dwonward slope from data
st.detrend(type="demean") #centers the data around 0

st[0].normalize().data #Normalizes data 
st.filter("bandpass", freqmin=1, freqmax=10)

# Read in fryxell miniseed

fryxell = read('fryxell_deployment.mseed')
fryxell = fryxell.copy()
#Filter Fryxell miniseed
fryxell.filter('bandpass', freqmin = 1, freqmax = 10)
f = fryxell[0].slice(date1, date2) #BHE seems clearest
# f.plot()
# f[0].spectrogram()

combined=f+st
combined.merge()
