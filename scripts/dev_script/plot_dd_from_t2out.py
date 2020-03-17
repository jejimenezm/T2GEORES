from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from model_conf import *
import pandas as pd
import sqlite3


parameter="P"
well="AH-1"
layer="D"

if parameter  not in ["P","T","SG","SW","X(WAT1)","X(WAT2)","PCAP","DG","DW"]:
	print "Cant be printed, the parameter is  not register"
elif parameter=="P":
	parameter_label="Pressure"
	parameter_unit="bar"
elif parameter=="T":
	parameter_label="Temperature"
	parameter_unit="C"
elif parameter=="SW":
	parameter_label="1-Quality"
	parameter_unit=""
elif parameter=="SG":
	parameter_label="Quality"
	parameter_unit=""
elif parameter=="DG":
	parameter_label="Density"
	parameter_unit="kg/m3"
elif parameter=="DW":
	parameter_label="Density"
	parameter_unit="kg/m3"
else:
	parameter_label=""
	parameter_unit=""

#Read file, calculated
file="../output/PT/evol/%s_PT_%s_evol.dat"%(well,layer)
data=pd.read_csv(file)

times=data['TIME']

values=data[parameter]

dates=[]
values_to_plot=[]
for n in range(len(times)):
	if float(times[n])>0:
		try:
			dates.append(ref_date+datetime.timedelta(days=int(times[n])))
			if parameter!="P":
				values_to_plot.append(values[n])
			else:
				values_to_plot.append(values[n]/1E5)
		except OverflowError:
			print ref_date,"plus",str(times[n]),"wont be plot"

conn=sqlite3.connect(db_path)
c=conn.cursor()

depth=pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%layer,conn)

depth=depth.values[0][0]

#Read file, real
file="../input/drawdown/%s_DD.dat"%well
data_real=pd.read_csv("../input/drawdown/%s_DD.dat"%well)
data_real.loc[data_real['TVD']==depth]['datetime']
dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
dates_real=list(map(dates_func,data_real.loc[data_real['TVD']==depth]['datetime'].values))

#Plotting

fig, ax = plt.subplots(figsize=(10,4))
ax.plot(dates,values_to_plot,'ob',linewidth=1,ms=3,label='Calculated drawdown')
ax.plot(dates_real,data_real.loc[data_real['TVD']==depth]['pressure'].values,'or',linewidth=1,ms=3,label='Real drawdown')
ax.set_title("Well: %s at %s masl (layer %s)"%(well,depth,layer) ,fontsize=8)
ax.set_xlabel("Time",fontsize = 8)
ax.set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)

ax.legend(loc="upper right")

#Plotting formating
xlims=[min(dates)-timedelta(days=365),max(dates)+timedelta(days=365)]
ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

years = mdates.YearLocator()
years_fmt = mdates.DateFormatter('%Y')

ax.set_xlim(xlims)
ax.xaxis.set_major_formatter(years_fmt)

#ax.xaxis.set_major_locator(years)
#fig.autofmt_xdate()

#Grid style
ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
ax.grid(True)

plt.show()