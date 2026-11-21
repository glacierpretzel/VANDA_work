from obspy import *
from obspy.signal.cross_correlation import correlation_detector
import pandas as pd
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
import matplotlib.dates as mdates
import numpy as np
import datetime
import seaborn as sns
import calendar
import argparse


def interevent_spacing(df):
    '''
    Definition for plotting a histogram of interevent spacing. 
    Option to group by month. 
    '''
    
    num_months = int(df['month'].nunique())
    #filt_min = filtered_df['interevent_time'].dt.total_seconds()/60
    print(f'there are {num_months} months')
    fig, ax = plt.subplots(num_months+1, figsize=(10, 8))
    #bins = 80
    for i , month in enumerate(df['month'].unique(), start = 0):
        #month = trigger_df[trigger_df.index.month == month]
        #interevent_spacing = trigger_df['interevent_time'].dt.total_seconds()/60
        data = df[df['onset'].dt.month == month][['interevent_time']]
        print(month)
        data.dropna()
        a = data['interevent_time'].dt.total_seconds()/60
        clean_a = a[np.isfinite(a)]
        filt_min = round(data.mean(),2)
        color = sns.color_palette()
        #print(data), print(type(data))
        #monthly_triggers = trigger_df.groupby(trigger_df['onset'].dt.to_period('M'))['interevent_time']
        bins = np.histogram_bin_edges(clean_a, bins="auto")
        #print(bins)
        #ax.scatter(pd.to_datetime(df['onset']).dt.date.unique(), daily_utc)
        ax[i].hist(a, bins = bins, edgecolor = 'black', label = f'trigger counts for month {month}', color = color[i])
        ax[i].axvline(x = filt_min.iloc[0].total_seconds()/60, color = 'black', linestyle = '--', linewidth = 2, label = f'{round(filt_min.iloc[0].total_seconds()/60,2)} minutes')
        sns.kdeplot(a,color = color[i], ax = ax[-1], label = f'average {round(filt_min.iloc[0].total_seconds()/60,2)} minutes')
        ax[i].legend()
        ax[i].set_xlim(0, 45)
        ax[-1].set_xlim(0, 45)
        ax[i].set_xticklabels([])
        ax[i].set_xticks([])
    fig.supxlabel('Time in Minutes')
    
    fig.tight_layout()
    fig.suptitle("Interevent Spacing", ha='center', va='top')
    fig.subplots_adjust(top=0.88)
    fig.supylabel('Occurances')
    #fig.suplegend()
    plt.show()
    return fig,ax
    
    
def hist_outline(dfs):
    fig, ax = plt.subplots(figsize=(10, 8))
    for d,df in enumerate(dfs):
        name = ['correlation', 'triggers']
        month_dict = {i: calendar.month_name[i] for i in range(1, 13)}
        num_months = int(df['month'].nunique())
        color = sns.color_palette()
        #filt_min = filtered_df['interevent_time'].dt.total_seconds()/60
        print(f'there are {num_months} months')
        
        #bins = 80
        for i , month in enumerate(df['month'].unique(), start = 0):
                #month = trigger_df[trigger_df.index.month == month]
                #interevent_spacing = trigger_df['interevent_time'].dt.total_seconds()/60
                #print(month)
            data = df[df['onset'].dt.month == month][['interevent_time']]
            data.dropna()
                
            a = data['interevent_time'].dt.total_seconds()/60
            clean_a = a[np.isfinite(a)]
            filt_min = round(data.mean(),2)
            #color = sns.color_palette()
            
            #print(data), print(type(data))
            #monthly_triggers = trigger_df.groupby(trigger_df['onset'].dt.to_period('M'))['interevent_time']
            bins = np.histogram_bin_edges(a=clean_a, bins='auto')
            #print(bins)
            #ax.scatter(pd.to_datetime(df['onset']).dt.date.unique(), daily_utc)
            #ax[i].hist(a, bins = bins, edgecolor = 'black', label = f'trigger counts for month {month}', color = color[i])
            #ax.axvline(x = filt_min.iloc[0].total_seconds()/60, color = 'black', linestyle = '--', linewidth = 2, label = f'{round(filt_min.iloc[0].total_seconds()/60,2)} minutes')
            sns.kdeplot(a,color = color[d], fill = True, label = f'{name[d]} {month_dict[month]} average {round(filt_min.iloc[0].total_seconds()/60,2)} minutes')
    ax.legend()

    #ax.set_xlim(0, 45)
    #ax.set_xticklabels([])
    #ax.set_xticks([])
    ax.set_xlabel("Time (min)")

    #fig.supxlabel('Time in Minutes')

    fig.tight_layout()
    fig.suptitle(" Histogram for Intervent Trigger Spacing", ha='center', va='top')
    fig.subplots_adjust(top=0.88)
    #fig.supylabel('Occurances')
    #fig.suplegend()
    plt.show()
    return fig, ax

def stat_plotter(df, df1):
    
    #Calculate hourly/daily metrics
    hourly_counts = df.groupby(df['local'].dt.hour).size() #in local time
    hour_utc = df.groupby(df['onset'].dt.hour).size() #UTC
    daily_counts = df.groupby(df['local'].dt.date).size() #in local time
    daily_utc = df.groupby(df['onset'].dt.date).size()

    #Plot hourly variation of signal detection
    fig, ax = plt.subplots()
    ax.scatter(df['hour_local'].unique(), hourly_counts, label = 'correlation') #local time
    ax.set_xlabel('Hours in Local Time (UTC+13)')
    ax.set_ylabel('Number of Triggers')
    #ax.set_ylim(50,200)
    ax.scatter(df1['hour_local'].unique(), df1.groupby(df1['local'].dt.hour).size(), color = 'red', label = 'triggers') #local time
    ax.legend()
    fig.suptitle('Triggers Grouped by Time of Day correlation vs filtered')

    #fig, ax = plt.subplots()
    #ax.scatter(df['hour_UTC'].unique(), hour_utc) #UTC time
    #ax.set_xlabel('Hours in UTc Time')
    #ax.set_ylabel('Number of Triggers')
    #ax.set_title('Triggers Grouped by Time of Day (UTC)')
    #plt.show()
    
    
    #pick_5 = daily_utc/(24*60) #event time put y-axis in pick per 5 ish min, or pick per minute
    fig, ax = plt.subplots()
    #ax.scatter(pd.to_datetime(df['onset']).dt.date.unique(), daily_utc)
    ax.scatter(pd.to_datetime(df['onset']).dt.date.unique(), daily_utc/(24), label = 'correlation') #pick per hour
    ax.scatter(pd.to_datetime(df['onset']).dt.date.unique(), df1.groupby(df1['onset'].dt.date).size()/24, color = 'red', label = 'Triggers')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.set_xlabel('Days in UTC Time')
    #ax.set_ylim(5,15)
    ax.set_title("Average Number of Events per Hour")
    ax.set_ylabel('Number of Triggers per Hour')
    ax.legend()
    
    fig.tight_layout(pad=3.0) 

    fig.add_gridspec(4, 4, wspace=0, hspace=0)
   
    #interevent time plot
   
    fig, ax = plt.subplots()
    #ax.scatter(pd.to_datetime(df['onset']).dt.date.unique(), daily_utc)
    ax.hist(df['interevent_time'].dt.total_seconds()/60, bins = 'auto', edgecolor = 'black', label = 'correlation') 
    ax.hist(df1['interevent_time'].dt.total_seconds()/60, bins = 'auto', edgecolor = 'black', color = 'red', label = 'triggers')
    #ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.set_xlabel('Time in Minutes')
    ax.set_title("Interevent Spacing")
    ax.set_ylabel('Occurances')
    ax.legend()
    plt.show()
    
    #rolling averages
    df_rolling = df[['onset', 'interevent_time']].set_index('onset')
    df_rolling['interevent_time'] = df_rolling['interevent_time'].dt.total_seconds()
    
    df1_rolling = df1[['onset', 'interevent_time']].set_index('onset')
    df1_rolling['interevent_time'] = df1_rolling['interevent_time'].dt.total_seconds()
    
    rolling_avg_df = df_rolling.rolling('600s').mean()
    rolling_avg_df1 = df1_rolling.rolling('600s').mean()
    
    fig, ax = plt.subplots()
    
    rolling_avg_df.plot(ax=ax, color = 'red')
    rolling_avg_df1.plot(ax=ax, color = 'blue')
    
    ax.legend(['Triggers', 'Correlation'])
    ax.set_ylabel('10 minute rolling average of interevent time (seconds)')
    fig.suptitle('WORK IN PROGRESS 10 min rolling average of comparing picker and correlator')
    plt.show()
    
    return fig, ax

