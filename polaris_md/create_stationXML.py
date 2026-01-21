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
digi_resp = "GüralpMinimus_×1_100_Hz_Acausal.RESP"
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

#Medatdata
lat = -77.6098
lon = 163.1698
elevation = 90
depth = 0.
start_date = UTCDateTime("1990-01-01")
end_date = UTCDateTime()

#Add Station name
inv_new[0].code = "DV" #network
inv_new[0].start_date = start_date
inv_new[0].end_date = end_date

inv_new[0][0].code = '01' #station
inv_new[0][0]._total_number_of_channels = 3
inv_new[0][0]._selected_number_of_channels = 3


# inv_new[0][0]._latitude = -77.72 #latitude
inv_new[0][0][0]._location_code = 'OL' #location
#Need to add 2 more channels
inv_new[0][0][0]._code ='HHZ' #channel code 
HHN=Channel(code="HHN",
            location_code='0L',
            latitude=lat,
            longitude=lon,
            elevation=elevation,
            depth=depth
            )

HHE=Channel(code="HHE",
            location_code='0L',
            latitude=lat,
            longitude=lon,
            elevation=elevation,
            depth=depth
            )

inv_new[0][0].channels.append(HHN)
inv_new[0][0].channels.append(HHE)



# inv_new[0].stations[0].latitude = "-77.61"
# inv_new[0].stations[0].longitude = "163.16"
# inv_new[0].stations[0].elevation = "90" #elevation of Lake fryxellin meters

# Write-out the new response
print('new network stuff', inv_new)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
# Write-out stationXML

# 2. Create a Network object and specify its stations list

inv_new.write("polaris.xml", format="STATIONXML")
