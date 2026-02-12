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
trigger_on = 4.0
trigger_off = 1.0
#----------------------------------------------------

args = create_parser().parse_args()

date1 = UTCDateTime(args.date1)
date2 = UTCDateTime(args.date2)

# Attach to client
client = Client(base_url='http://10.30.5.28:8080',
                debug=True, user='ken', password='grayling')

client2 = Client('IRIS')

# Get data
try:
    st = client.get_waveforms(
        station='VNDA',
        network='*',
        location='*',
        channel='BHZ',
        starttime=date1,
        endtime=date2,
    )
except:
    print("Unable to get data!")
    sys.exit()

# Preprocessing
st.merge(fill_value = 'interpolate')
st.detrend(type="linear")
st.detrend(type="demean")
st.filter("bandpass", freqmin=5, freqmax=20)

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
    cat = client2.get_events(starttime = date1, endtime = date2,  minmagnitude = 6, maxmagnitude = 9)
except:
    print('No earthquakes for this time period.')
    cat = 0
    
at = []
if cat != 0:
    # Earth model for move-out correction
    model = TauPyModel(model="iasp91")
    for c in cat:
        print("Working on %s = %1.1f event...\n" % (c.magnitudes[0].magnitude_type, 
	                                        c.magnitudes[0].mag))
        sta_lo = 161.878200
        sta_la = -77.512369
        
        # Compute the offset
        d, az, baz = gps2dist_azimuth(c.origins[0].latitude, c.origins[0].longitude, sta_la, sta_lo)
        dgs = kilometer2degrees(d/1000)
        d_km = d/1000
        # Find the arrival time
        p_arrivals = model.get_travel_times(source_depth_in_km = c.origins[0].depth/1000,
                                            distance_in_degree = dgs,
                                            phase_list = ["P", "p"])
    
        # Define the moveout
        p0 = c.origins[0].time + p_arrivals[0].time
        at.append(p0)
	
# Print trigger times in UTCDateTime format
print("Detected triggers:")
trig_times = []
onset_times = []
for trigger in triggers:
    onset = st[0].stats.starttime + trigger[0] / sr
    offset = st[0].stats.starttime + trigger[1] / sr
    print(f"Trigger from {onset} to {offset}")

    # Filter
    if len(at) > 0:
        for a in at:
            if abs(onset - a) > 10:
                onset_times.append(onset)
            else:
                print('Skipping onset time because it is probably an earthquake', onset)
    trig_times.append([onset, offset])

# Plot the results ------------------------------

fig, ax = plt.subplots(1)

# Plot the waveform
st[0].taper(0.01)
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
ax.set_ylabel('counts')
ax.set_xlabel('%s [UTC]' % st[0].stats.starttime.strftime('%Y-%M-%d'))
ax.legend()
tfmt = mdates.DateFormatter('%H:%M')
ax.xaxis.set_major_formatter(tfmt)
ax.xaxis_date()
# Turn on a grids
ax.grid(True, 'both')     
# Title
ax.title.set_text('VNDA Weirdness')
plt.show()

# Save results to text file
s1 = date1.strftime('%Y-%M-%dT%H-%m')
s2 = date2.strftime('%Y-%M-%dT%H-%m')
nme = 'onset_times' + '_' + s1 + '_' + s2 + '.txt'
with open(nme, "w") as file:
    for time in onset_times:
        file.write(str(time) + "\n")
