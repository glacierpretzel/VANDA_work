from obspy import *
from obspy.signal.cross_correlation import correlation_detector
import pandas as pd
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
import numpy as np
import datetime
import argparse
import os
from vnda_picker_orig import picker
from hist_outline import *
#print('LENGTH of SLICED_WVF', len(sliced_wvf))


def create_parser():
    parser = argparse.ArgumentParser(description="Use Obspy to plot waveforms.")
    parser.add_argument(
        "template_list",
        nargs="+",
        help="Space-separated list of template names or file paths.")

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
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate plot ",
    )


    return parser
    
def dataframe_creator(trig_times, peak_amps):
    import pandas as pd
    df = pd.DataFrame(trig_times)
    df.rename(columns={df.columns[0]: 'onset'}, inplace=True)
   
    df['peak_amps m'] = peak_amps
    #trigger_df.set_index()
    df['onset'] = [t.datetime for t in df['onset']]
    #trigger_df[1] = [t.datetime for t in trigger_df[1]]
    df['month'] = df['onset'].dt.month
    df['day'] = df['onset'].dt.day
    df['hour_UTC'] = df['onset'].dt.hour
    #Times in local Antarctica time, better for daylight tracking, diurnal patterns
    df['local'] = df['onset'].dt.tz_localize('UTC').dt.tz_convert('Antarctica/McMurdo')
    df['hour_local'] = df['local'].dt.hour
    df['day_local'] = df['local'].dt.day
    
    #trigger_df.rename(columns={0:'onset'}, inplace = True)
    
    #Interevent spacing
    df['interevent_time'] = df['onset'].shift(-1) - df['onset']
    
    #Hourly and Daily counts
    df["hourly_counts"] = df.groupby(df['local'].dt.hour).size() #in local time
    hour_utc = df.groupby(df['onset'].dt.hour).size() #UTC
    daily_counts = df.groupby(df['local'].dt.day).size() #in local time
    daily_utc = df.groupby(df['onset'].dt.day).size()
    #trigger_df['amplitude m'] = pd.DataFrame(peak_amps) #amplitude - displacement in meters
    
    #Filtered to no events under 2 minute interspacing
    filtered_df = df[df['interevent_time'].dt.total_seconds() > 120]
    return df, filtered_df
    
def correlator(template_str, trig_times, peak_amps):
    """
    Calculates the correlation of a stream object with selected templates 
    Outputs: list of Pd dataframe of the correlations. 
    """
    trig_times = trig_times
    peak_amps=peak_amps
    templates = []
    template_magnitudes = []
    for template in template_str:
        #print(template)
        t = read(template)
        templates.append(t)
        template_magnitudes.append(float(max(t[0])))
    
    detection_time= []
    corrs = []
    mags = []
    more_ds = []
    
    for i, template in enumerate(templates):
        #template = test_temp
        
        #height = [0.4,0.8,0.1]
        height = [0.4]
        ds = []
        d = []
        c = []
        m = []
        for h in height:
            distance = len(templates[i][0])
            
            detections, corr = correlation_detector(st, template, h, distance, template_magnitudes=template_magnitudes, template_names = i)
            more_ds.append(detections)
            for det in detections:
            
                d.append(det['time'])
                c.append(det['similarity'])
                m.append(det['magnitude'])
            print(f'TEMPLATE {i} {template[0].stats.starttime}')
            print(f'NUMBER of DETECTIONS {len(detections)}') 
            #print(f'AMPS {mean(detections)}') 
        #more_ds.append(ds)
        detection_time.append(d)
        corrs.append(c)
        mags.append(m)
    

    output_dir = 'data'
    file_corr = []
    file_filt_corr = []
    for i, d in enumerate(more_ds):

        if len(d)>0:
            print('Making dataframe with correlations')
            CORR_df, FILTERED_corr = dataframe_creator(d, mags[i])
            if not CORR_df.empty:
                
                file_name_corr = CORR_df['onset'].iloc[0].strftime('%Y-%m-%dT%H:%M:%S')
                file_corr.append(CORR_df)
                CORR_df.to_csv(os.path.join(output_dir, f"CORR_{file_name_corr}.csv"))
            else:
                print(f"No events found for CORR_df on template {i}")
                
            if not FILTERED_corr.empty:
                print('Making dataframe with filtered correlations')
                file_name_filt = FILTERED_corr['onset'].iloc[0].strftime('%Y-%m-%dT%H:%M:%S')
                file_filt_corr.append(FILTERED_corr)
                FILTERED_corr.to_csv(os.path.join(output_dir, f"FILT_{file_name_filt}.csv"))
            else:
                print(f"No events found for FILTERED_corr on template {i}")
        else:
            print(f'template {i+1} has no entries in its detections.')
    return file_corr, file_filt_corr


    
args = create_parser().parse_args()

template_list = args.template_list
date1 = UTCDateTime(args.date1)
date2 = UTCDateTime(args.date2)
plot = args.plot

print('Start', date1, 'Stop', date2, 'Plot?', plot)

# calls the sta/lta picker function from vnda_picker_org.py returning the data strea, trig, times, peak_amps, and all the sliced_wvfs
st, trig_times, peak_amps, sliced_wvf = picker(date1, date2, plot)
#Calculating the trigger/filtered_picker dataframes
trigger_df, filtered_df = dataframe_creator(trig_times, peak_amps)
output_dir = 'data'
filtered_df.to_csv(os.path.join(output_dir, f"Trig_filt_{filtered_df['onset'][1]}.csv"))
trigger_df.to_csv(os.path.join(output_dir, f"Trigs_{trigger_df['onset'][1]}.csv"))

#Now calculate the correlations
file_corr, file_filt_corr = correlator(template_list, trig_times, peak_amps)

#Let's plot! oh who am I kidding. it's more like, let's plot.
for file in file_corr:
    
    stat_plotter(trigger_df, file)

