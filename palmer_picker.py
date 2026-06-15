import sys
from obspy import *
from obspy.signal.trigger import classic_sta_lta, trigger_onset
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
import matplotlib.dates as mdates
import argparse
#from obspy.taup import TauPyModel
from obspy.geodetics.base import gps2dist_azimuth
from obspy.geodetics.base import kilometer2degrees
from scipy.signal.windows import hann
import pandas as pd
import numpy as np

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

#----------------------------------------------------
# Picker thresholds - these will need to be tweaked:
trigger_on = 4.8 # looks like the happy spot
trigger_off = 1.0
#----------------------------------------------------

args = create_parser().parse_args()

date1 = UTCDateTime(args.date1)
date2 = UTCDateTime(args.date2)

# Attach to client
client2 = Client(base_url='http://10.30.5.28:8080',
                 debug=True, user='ken', password='grayling')

#client2 = Client('FDSN')

# Get data
try:
    st = client2.get_waveforms(
        station='I54H2',
        network='*',
        location='*',
        channel='BDF',
        starttime=date1,
        endtime=date2,
        attach_response=True
    )
except:
    print("Unable to get data!")
    sys.exit()

# Preprocessing
sr = st[0].stats.sampling_rate

pre_filt = [0.001, 0.005, sr / 2 - 2, sr / 2]
st.remove_response(output = 'DISP', pre_filt = pre_filt, taper=False)
st.merge(fill_value = 'interpolate')
st.detrend(type="linear")
st.detrend(type="demean")
#st[0].taper(0.01)
st.filter("bandpass", freqmin=2, freqmax=8)

# Set-up triggers
sr = st[0].stats.sampling_rate

# Define STA and LTA window lengths (in samples)
nsta = int(0.5 * sr)  # Short-term window: 0.5 seconds
nlta = int(3 * sr)    # Long-term window: 3 seconds

# Calculate the STA/LTA characteristic function
cft = classic_sta_lta(st[0].data, nsta, nlta)

# Identify trigger onsets and offsets as sample indices

triggers = trigger_onset(cft, trigger_on, trigger_off)

try:
    # Find events
    cat = client2.get_events(starttime = date1, endtime = date2,  minmagnitude = 5, maxmagnitude = 9)
except:
    print('No earthquakes for this time period.')
    cat = 0
    
# Print trigger times in UTCDateTime format

trig_times = []
onset_times = []
peak_amps = []
sliced_wvf = []

for trigger in triggers:
    onset = st[0].stats.starttime + trigger[0] / sr
    offset = st[0].stats.starttime + trigger[1] / sr
    #slicing the waveform on the onset and offset trigger times. This will be useful for template matching. 
    sliced = st[0].slice(onset,offset)
    
    if len(sliced)>0:
        #Filtering by max amplitude. 
        max_amp = max(abs(sliced.data))
        
        if max_amp>3E-3:
            trig_times.append([onset, offset])
            peak_amps.append(max_amp)
            
                #Making first waveform slightly shorter than the rest of them so I can manually make families for template matching
            sliced_wvf.append(st[0].slice(onset-1,offset+10))
            
        else: 
            #print(f'max amp too small, {max_amp}')
            pass
# Plot the results ------------------------------
plot = Fals
if plot ==True:
    fig, ax = plt.subplots(1)
    
    # Plot the waveform
    st[0].taper(0.01)
    start = st[0].stats.starttime
    #time = np.range(start, start+60*60, len(st[0].data))
    ax.plot(st[0].times("matplotlib"), st[0].data, "k-", label = st[0].stats.channel)
    
    # Plot the triggers
    k = 0
    for t in trig_times:
        t1 = mdates.date2num(t[0].datetime)
        t2 = mdates.date2num(t[1].datetime)
        if k == 0:
            ax.axvspan(t1, t2, color="red", alpha=0.3, label="Trigger")
        else:
            ax.axvspan(t1, t2, color="red", alpha=0.3)
        k = k + 1
    
    # Labels and such
    ax.set_ylabel('Displacement m')
    ax.set_xlabel('%s [UTC]' % st[0].stats.starttime.strftime('%Y-%m-%d'))
    ax.legend()
    tfmt = mdates.DateFormatter('%H:%M:%S')
    fig.autofmt_xdate(rotation=45)
    ax.xaxis.set_major_formatter(tfmt)
    ax.xaxis_date()
    # Turn on a grids
    ax.grid(True, 'both')     
    # Title
    ax.title.set_text('I54US Signals')
    plt.show()
    


    
    


# Save results to text file
#s1 = date1.strftime('%Y-%M-%dT%H-%m')
#s2 = date2.strftime('%Y-%M-%dT%H-%m')
#nme = 'onset_times' + '_' + s1 + '_' + s2 + '.txt'
#with open(nme, "w") as file:
    #for time in trig_times:
        #file.write(str(time) + "\n")


