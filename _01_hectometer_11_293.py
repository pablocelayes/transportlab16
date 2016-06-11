
import pandas as pd
import csv
from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np

################################################################################
# INPUTS

times = pd.date_range(start = datetime(2011, 1, 1), end = datetime(2011, 12, 31, 23, 59), freq = 'T')

# Hectometers
with open('../Rechts_Hectometerpalen_2011.csv', 'r') as f:
    rh = [i[0] for i in csv.reader(f)]

rSpeed = pd.read_csv('../Rechts_Speed_2011.csv', names = rh)

jamSpeedThreshold = 60# speed under which we define a traffic jam
jamTimeThreshold = 60# minutes under jamSpeed with which we define a jam in a day

fOutJamFreeDays = 'jamFreeDays_speed_%i_time_%i.pickle' % (jamSpeedThreshold, jamTimeThreshold)
fOutMorningJamDays = 'morningJDays_speed_%i_time_%i.pickle' % (jamSpeedThreshold, jamTimeThreshold)
fOutAfternoonJamDays = 'afternoonJDays_speed_%i_time_%i.pickle' % (jamSpeedThreshold, jamTimeThreshold)



################################################################################
# FUNCTIONS

def jitterBoxPlot(ax, dataDict, keyList, labels = []):
    """
    Creates a boxplot and draw a jitter plot with the data
    points on top.
    
    ACCEPTS:
        dataDict [dict] {category : data [1d array or list]}
        keyList [list] ordered in which the categories will be plotted
        labels [list] list of labels (if keys aren't wanted)
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
del(rSpeed)
df['dayofyear'] = df.index.dayofyear
df['dayofweek'] = df.index.dayofweek
df['hour'] = df.index.hour
df['jam'] = (df['11.293'] < jamSpeedThreshold)*1

##################
# On which days of the week do traffic jams occur most often?

# Grouping by day of the year
byDay = df.groupby('dayofyear')
jamTime = (byDay['jam'].sum())
jamDay = byDay['dayofweek'].min()

jamDf = pd.DataFrame({'day' : jamDay, 'totalJamTime' : jamTime}, index = jamTime.index)

# group by day of the week
byDayOfWeek = jamDf.groupby('day')
indicesByDayOfWeek = byDayOfWeek.groups

jamByDay = {}
for key in indicesByDayOfWeek:
    jamByDay[key] = jamDf['totalJamTime'][indicesByDayOfWeek[key]]

####################
# At what times during the day do traffic jams occur most often?

# Groping by hour of the day, excluding weekends
dfWeekdays = df[df['dayofweek'] < 5][['11.293', 'hour', 'dayofyear']]
dfWeekdays['jam'] = (dfWeekdays['11.293'] < jamSpeedThreshold)*1

jamsByHour = dfWeekdays.groupby('hour').mean()

####################
# On which days in 2011 did traffic jams occur?

# Cumulated sum reseted each time zero appears. For finding contigous
# streches of time with speers below jamSpeed
cs_withReset = []
c = 0
for i in dfWeekdays['jam'].values:
    if i == 0:
        c = 0
    else:
        c += 1
    cs_withReset.append(c)
dfWeekdays['cumSum'] = cs_withReset

jamsIn2011 = dfWeekdays[dfWeekdays['cumSum'] > jamTimeThreshold].groupby('dayofyear').max()
jamsIn2011.reset_index(inplace = True)
afternoonJamDays =  jamsIn2011[jamsIn2011['hour'] > 12]['dayofyear'].values
morningJamDays =  jamsIn2011[jamsIn2011['hour'] < 12]['dayofyear'].values
withoutJams = [day for day in dfWeekdays['dayofyear'].unique() if day
        not in np.concatenate((afternoonJamDays, morningJamDays))]


#jamsIn2011 = dfWeekdays.groupby('dayofyear').sum()
#jamsIn2011 = jamsIn2011[jamsIn2011['jam'] > jamTime] 

# Defining a jam as a day in which more than 60 minutes are spend at speeds
# below 30 km/h yields 77 of the 260 weekdays in 2011 (30%) as days with 
# traffic jams

################################################################################
# OUTPUTS

# PLOTS

fig, ax = plt.subplots(nrows = 2, ncols = 1)
jitterBoxPlot(ax[0], jamByDay, jamByDay.keys(), labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
ax[0].set_ylabel('Minutes at speeds below %i km/h' % jamSpeedThreshold)

ax[1].bar(np.arange(24)+0.1, jamsByHour['jam'].values)
ax[1].set_xlabel('Time of day [h]')
ax[1].set_ylabel('Av. mins per hour in jams')
ax[1].set_xticks(range(24))
ax[1].set_xticklabels(range(24))
ax[1].set_xlim(0,24)
fig.show()


# Exporting dataframes with jam free days, days with morning jams and days with afternoon jams.

print("days with both moring and afternoon jams: ", set(afternoonJamDays) & set(morningJamDays))

dfJamFree = dfWeekdays[dfWeekdays['dayofyear'].isin(withoutJams)]
dfMorningJams = dfWeekdays[dfWeekdays['dayofyear'].isin(morningJamDays)]
dfAfternoonJams = dfWeekdays[dfWeekdays['dayofyear'].isin(afternoonJamDays)]

dfJamFree.to_pickle(fOutJamFreeDays)
dfMorningJams.to_pickle(fOutMorningJamDays)
dfAfternoonJams.to_pickle(fOutAfternoonJamDays)





