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
client = Client(base_url='http://10.30.5.28:8080',
                 debug=True, user='ken', password='grayling')

#client2 = Client('EARTHSCOPE')

# Get data
try:
    st = client.get_waveforms(
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
st1 = Stream()
bold_trigs = []
for trace in st:

    sr = trace.stats.sampling_rate
    pre_filt = [0.001, 0.005, sr / 2 - 2, sr / 2]
    trace.remove_response(output = 'DISP', pre_filt = pre_filt)
    trace.taper(0.05)
    # Define STA and LTA window lengths (in samples)
    nsta = int(0.5 * sr)  # Short-term window: 0.5 seconds
    nlta = int(3 * sr)    # Long-term window: 3 seconds

    # Calculate the STA/LTA characteristic function
    cft = classic_sta_lta(st[0].data, nsta, nlta)

    # Identify trigger onsets and offsets as sample indices
    triggers = trigger_onset(cft, trigger_on, trigger_off)
    bold_trigs.append(triggers)
    trace.filter("bandpass", freqmin=1, freqmax=8)
    st1.append(trace)
st1.merge(fill_value = 'interpolate')

st1.detrend(type="linear")
st1.detrend(type="demean")

#try:
    # Find events
    #cat = client2.get_events(starttime = date1, endtime = date2,  minmagnitude = 3, maxmagnitude = 9)
#except:
    #print('No earthquakes for this time period.')
    #cat = 0
    
# Print trigger times in UTCDateTime format
#Palmer triggers
all_trigs = []

for trace in st1:
    print(trace)
    trig_times = []
    onset_times = []
    sliced_wvf = []
    for array in bold_trigs:
        for trigger in array:
            onset = trace.stats.starttime + trigger[0] / sr
            offset = trace.stats.starttime + trigger[1] / sr
            #slicing the waveform on the onset and offset trigger times. This will be useful for template matching. 
            sliced = st[0].slice(onset,offset)
            if len(sliced)>0:
                #Filtering by max amplitude. 
                max_amp = max(abs(sliced.data))
                
                if max_amp>0.5E-9:
                    trig_times.append([onset, offset])
                    #peak_amps.append(max_amp)
                    
                    sliced_wvf.append(st[0].slice(onset-20,offset+30))
                    if max_amp > 1.5E-8:
                        pass
                        #print(f'Thats a big one!')
                else: 
                    #print(f'max amp too small, {max_amp}')
                    pass
        all_trigs.append(trig_times)
#i54_trigs = all_trigs[0]
#pmsa_trigs = all_trigs[1]
# Plot the results ------------------------------
plot = False
if plot ==True:
    fig, ax = plt.subplots(2, layout = 'constrained')
    
    # Plot the waveform
    #st[0].taper(0.01)
    start = st[0].stats.starttime
    #time = np.range(start, start+60*60, len(st[0].data))
    ax[0].plot(st1[0].times("matplotlib"), st[0].data, "k-", label = st[0].stats.channel)
    ax[1].plot(st1[1].times("matplotlib"), st[1].data, "k-", label = st[1].stats.channel)
    
    # Plot the triggers
    k = 0
    for t in i54_trigs:
        t1 = mdates.date2num(t[0].datetime)
        t2 = mdates.date2num(t[1].datetime)
        if k == 0:
            ax[0].axvspan(t1, t2, color="red", alpha=0.3, label="Trigger")
        else:
            ax[0].axvspan(t1, t2, color="red", alpha=0.3)
        k = k + 1
    
    c = 0
    for t in pmsa_trigs:
        t1 = mdates.date2num(t[0].datetime)
        t2 = mdates.date2num(t[1].datetime)
        if k == 0:
            ax[1].axvspan(t1, t2, color="red", alpha=0.3, label="Trigger")
        else:
            ax[1].axvspan(t1, t2, color="red", alpha=0.3)
        c = c + 1
        
    # Labels and such
    ax[0].set_ylabel('Displacement m')
    ax[1].set_ylabel('Displacement m')
    ax[0].set(xlabel = None)
    ax[1].set_xlabel('%s [UTC]' % st[0].stats.starttime.strftime('%Y-%m-%d'))
    ax[1].legend()
    tfmt = mdates.DateFormatter('%H:%M:%S')
    ax[1].xaxis.set_major_formatter(tfmt)
    ax[1].xaxis_date()
    # Turn on a grids
    #fig.set_grid(True, 'both')     
    # Title
    ax[0].title.set_text('I54H2 Signals')
    ax[1].title.set_text('PMSA Signals')
    fig.autofmt_xdate(rotation=45)
    

    
    plt.show()

    
    


# Save results to text file
#s1 = date1.strftime('%Y-%M-%dT%H-%m')
#s2 = date2.strftime('%Y-%M-%dT%H-%m')
#nme = 'onset_times' + '_' + s1 + '_' + s2 + '.txt'
#with open(nme, "w") as file:
    #for time in trig_times:
        #file.write(str(time) + "\n")


