
import pandas as pd
import csv
from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np

################################################################################
# INPUTS
#fOutRechts = 'rechts_febFirst2weeks.pickle'

# testing edition

times = pd.date_range(start = datetime(2011, 1, 1), end = datetime(2011, 12, 31, 23, 59), freq = 'T')

# Hectometers
with open('Rechts_Hectometerpalen_2011.csv', 'r') as f:
    rh = [i[0] for i in csv.reader(f)]

rSpeed = pd.read_csv('Rechts_Speed_2011.csv', names = rh)

jamSpeed = 30# speed underwhich we define a traffic jam
################################################################################
# FUNCTIONS

def jitterBoxPlot(ax, dataDict, keyList, labels = []):
    """
    Creates a boxplot and draw a jitter plot with the data
    points on top.
    
    ACCEPTS:
        dataDict [dict] {category : data [1d array or list]}
        keyList [list] ordered in which the categories will be plotted
    """
    from matplotlib import pyplot as plt
    from matplotlib.pyplot import boxplot, plot
    from numpy.random import uniform
    
    # retrieving the data in dataDict as a list of lists
    # the input of matplotlib's boxplot
    bpData = [[i for i in dataDict[key]] for key in keyList]
    #Draw boxplot without outliers
    ax.boxplot(bpData, showfliers = False)
    # draw the jitter plot
    for i, key in enumerate(keyList):
        x = uniform((i+1)*0.98, (i+1)*1.02, size = len(dataDict[key]))
        ax.plot(x, dataDict[key], 'k.')
    ax.set_xticks(range(1, len(keyList)+1))
    if labels:
        ax.set_xticklabels(labels)
    else:
        ax.set_xticklabels(keyList)

################################################################################
# STATEMENTS

# Missing values are indicates with zeros
rSpeed.replace(0, pd.np.nan, inplace = True)
# Adding time as index
rSpeed.set_index(times, inplace = True)

# NOTE, I can do this for all hectometers but I'll start with 12.293
df = pd.DataFrame(rSpeed['11.293'], index = rSpeed.index)
# Taking averages every 15 minutes
df = df.resample('15T').mean()

df['week'] = df.index.week
df['dayofyear'] = df.index.dayofyear
df['dayofweek'] = df.index.dayofweek
df['hour'] = df.index.hour
df['jam'] = (df['11.293'] < jamSpeed)*1

##################
# Grouping by day of the year
byDay = df.groupby('dayofyear')
jamTime = (byDay['jam'].sum())*15
jamDay = byDay['dayofweek'].min()
jamWeek = byDay['week'].min()

jamDf = pd.DataFrame({'week' : jamWeek, 'day' : jamDay, 'hour' : jamHour,'totalJamTime' : jamTime}, index = jamTime.index)

# group by day of the week
byDayOfWeek = jamDf.groupby('day')
indicesByDayOfWeek = byDayOfWeek.groups

jamByDay = {}
for key in indicesByDayOfWeek:
    jamByDay[key] = jamDf['totalJamTime'][indicesByDayOfWeek[key]]

fig, ax = plt.subplots(nrows = 2, ncols = 1)
jitterBoxPlot(ax[0], jamByDay, jamByDay.keys(), labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
ax[0].set_ylabel('Minutes at speeds below %i km/h' % jamSpeed)


####################

# Groping by hour of the day, excluding weekends
dfWeekdays = df[df['dayofweek'] < 5][['11.293', 'hour', 'dayofyear']]
dfWeekdays = dfWeekdays.resample('1H').mean()
dfWeekdays['jam'] = (dfWeekdays['11.293'] < jamSpeed)*1

jamsByHour = dfWeekdays.groupby('hour').mean()

ax[1].bar(np.arange(24), jamsByHour['jam'].values)
ax[1].set_xlabel('Time of day [h]')
ax[1].set_ylabel('fraction of jams (days of the week)')
fig.show()


# There is a jam (defiend as speed < 30 on an hour average) 26 out 260 weekdays
# i.e. 10% of the time
# most jams begin after 15h
# TASK: predict jams after 15h based on measurements from 0 to 14h

################################################################################
# OUPUTS
#rechts.to_pickle(fOutRechts)
#links.to_pickle(fOutLinks)


