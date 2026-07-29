# -----------------------------------------------------------------------------------------------------------------------------------------------------------------

import sys
import os
import numpy as np
from obspy import *
import argparse
import configparser
from scipy import signal
from obspy.core.inventory import *

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Read in the response files
digi_resp = "GüralpMinimus_×1_100_Hz_Acausal.RESP"
sens_resp = "NANOMETRICS_TC120HORIZON.RESP"

# Read into ObsPy inventory objects
inv_digi = read_inventory(digi_resp)
inv_sens = read_inventory(sens_resp)

# Response object
resp_digi = inv_digi[0][0][0].response
resp_sens = inv_sens[0][0][0].response

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Replace stage one of digitizer with sensor response
inv_new = inv_digi.copy()
resp_new = inv_new[0][0][0].response

resp_new.response_stages[0] = resp_sens.response_stages[0]

# We have introduced a new gain into stage 1,
# so we need to recalculate the overall gain.
# ObsPy makes this easy
resp_new.recalculate_overall_sensitivity()

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Now that we have the response we want, let's create a new inventory from scratch,
# then attach the new response

#Medatdata
lat = -77.6098
lon = 163.1698
elevation = 90
depth = 0.
start_date = UTCDateTime("2025-11-18T00:00:00.000000Z")
end_date = UTCDateTime()

desc = "Nanometrics TC120 Horizon seismometer"

#Add Station name
inv_new[0].code = "DV" #network
inv_new[0].start_date = start_date
inv_new[0].end_date = end_date

inv = Inventory(
    # We'll add networks later.
    networks=[],
    # The source should be the id whoever create the file.
    source="temporary deployment")

net = Network(
    # This is the network code according to the SEED standard.
    code="DV",
    # A list of stations. We'll add one later.
    stations=[],
    description="inventory for windless bight temp deployment",
    # Start-and end dates are optional.
    start_date=start_date)

sta = Station(
    # This is the station code according to the SEED standard.
    code="DV01",
    latitude=lat,
    longitude=lon,
    elevation=elevation,
    creation_date=UTCDateTime(),
    site=Site(name="DV Site")
    )

# Channels
cha=Channel(code="HHN",
            location_code='',
            start_date = start_date,
            latitude=lat,
            longitude=lon,
            elevation=elevation,
            depth=depth,
            azimuth=135,
            dip=0.0,
            sample_rate=100.0,
            sensor = Equipment(
                description=desc,
            )
            )
cha.response = resp_new
sta.channels.append(cha)
# Next channel
cha=Channel(code="HHE",
            location_code='',
            start_date = start_date,
            latitude=lat,
            longitude=lon,
            elevation=elevation,
            depth=depth,
            azimuth=90.0,
            dip=0.0,
            sample_rate=100.0,
            sensor = Equipment(
                description=desc,
            )
            )
cha.response = resp_new
sta.channels.append(cha)
# Next channel
cha=Channel(code="HHZ",
            location_code='',
            start_date = start_date,
            latitude=lat,
            longitude=lon,
            elevation=elevation,
            depth=depth,
            azimuth=0.0,
            dip=-90.0,
            sample_rate=100.0,
            sensor = Equipment(
                description=desc,
            )
            )
cha.response = resp_new
sta.channels.append(cha)

# Finish putting the inventory together
net.stations.append(sta)
inv.networks.append(net)

# Write-out the staxml
inv.write("DV_orr.xml", format="STATIONXML")
sys.exit()

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
# writing out new miniseed file
st=read('/Users/kitsellusted/Desktop/Dry_valley_data/*.mseed') 

for tr in st:  
    if len(tr)<=0:
        st.remove(tr)


wb = st.merge()
#Changing the station name to match the inventory object
#wb.remove(wb[0]) #Get rid of the BDF channel

wb[0].stats.network = 'DV' 
wb[1].stats.network = 'DV'
wb[2].stats.network = 'DV'

wb[0].stats.location = '' 
wb[1].stats.location = ''
wb[2].stats.location = ''

wb[0].stats.channel = 'HHE' 
wb[1].stats.channel = 'HHN'
wb[2].stats.channel = 'HHZ'
print(wb)

inv=read_inventory('WB.xml')
inv[0][0][0].azimuth = inv[0][0][0].azimuth + 135

wb.rotate(method = "->ZNE", inventory = inv)
# Attach Responsefor Dry Valley set-up
# Digi= Guralp Minimus Plus, Sensor = Nanometrics TCH120
print('attaching response')
wb.attach_response(inv) 

# Decon
sr = wb[0].stats.sampling_rate
pre_filt = [0.001, 0.005, sr / 2 - 2, sr / 2]
print('removing response')
wb.remove_response(pre_filt=pre_filt, output="DISP")
wb.detrend(type="linear") #removes upward/dwonward slope from data
wb.detrend(type="demean") #centers the data around 0
#applying bandpass filter
wb.filter('bandpass', freqmin = 1, freqmax = 20)

wb.write("fryxell_deployment.mseed", format="MSEED")

