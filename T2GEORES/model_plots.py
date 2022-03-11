from T2GEORES import geometry as geometry
from T2GEORES import formats as formats
from T2GEORES import t2geores_functions as t2funcs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import sys
import matplotlib.gridspec as gridspec
from iapws import IAPWS97
import os
from statsmodels.nonparametric.smoothers_lowess import lowess

import sqlite3

def plot_vertical_layer_distribution(show_fig,sav_fig,input_dictionary):
	"""It plots the layers defined for the mesh

	Parameters
	----------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'.
	show_fig: bool
	  If True shows the figure
	sav_fig: bool
	  If True saves the figure on ../output/

	Returns
	-------
	image
		vertical_distribution.png: output figure

	Examples
	--------
	>>> plot_vertical_layer_distribution(show_fig=True,sav_fig=False,input_dictionary)
	"""

	font_title_size=12
	fontsizey_layers=10
	fontsize_label=8

	layers_info=geometry.vertical_layers(input_dictionary)

	fig=plt.figure(figsize=(2.5, 8), dpi=100)

	ax=fig.add_subplot(111)
	y_layer_plot=layers_info['top']
	x_layer_plot=[100]*len(layers_info['top'])

	ax.plot(x_layer_plot,y_layer_plot,'-r',alpha=0)
	Depth_lims=[min(layers_info['bottom']),max(layers_info['top'])]

	ax.set_ylim(Depth_lims)
	ax.set_xlim([95,105])

	ax.set_ylabel('m.a.s.l.',fontsize = fontsizey_layers)
	ax.xaxis.tick_top()
	ax.tick_params(axis='x',which='both',length=0,labeltop=False)
	ax.title.set_position([0.5,1.05])
	ax.xaxis.set_label_coords(0.5,1.15)
	ax.yaxis.set_label_coords(-0.2,0.5)
	ax.tick_params(axis='y', which='major', labelsize=fontsize_label,pad=1)

	#Set layers

	ax2 = ax.twinx()            
	ax2.set_yticks(layers_info['top'], minor=True)
	ax2.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.6)
	ax2.set_yticks( layers_info['middle'], minor=False)
	ax2.set_yticklabels(layers_info['name'],fontsize=fontsize_label)
	ax2.tick_params(axis='y',which='both',length=0)
	ax2.set_ylabel('Layers',fontsize = fontsizey_layers)
	ax2.yaxis.set_label_coords(1.15,0.5)
	ax2.set_ylim(ax.get_ylim())
	plt.tight_layout()

	if show_fig:
		plt.show()
	if sav_fig:
		fig.savefig("../output/vertical_distribution.png", format='png',dpi=300)

def permeability_plot(input_dictionary,show_fig,sav_fig):
	"""It generates a plot for the permeability distribution. Currently just 'Corey' is available.

	Parameters
	----------
	input_dictionary: dictionary
	  Contains the permeability distribution information under the keyword of 'RPCAP'
	sav_fig: bool
	  If true saves the figure on ../output
	slr: float
	  Saturacion de liquido, tomado de model_conf

	Returns
	-------
	image
		coreys_permeabilities.png: output figure

	Examples
	--------
	>>> permeability_plot(input_dictionary,show_fig=True,sav_fig=True)
	"""

	IRP=input_dictionary['IRP']
	slr=input_dictionary['RP1']
	sgr=input_dictionary['RP2']

	fontsize_=26
	if IRP==3:

		krl=[]
		krg=[]
		saturation=[]
		plt.rcParams["font.family"] = "Times New Roman"

		for n in np.linspace(0,1,200):
			S=(n-slr)/(1-slr-sgr)
			to_krl=S**4
			to_krg=((1-S)**2)*(1-S**2)
			if to_krl>1:
				to_krl=1
			if to_krg>1:
				to_krg=1

			if n<slr and to_krg>0:
				to_krl=0

			if n<slr and to_krl>1:
				to_krl=1

			krl.append(to_krl)
			krg.append(to_krg)
			saturation.append(n)

		fig= plt.figure(figsize=(10, 10))
		ax1=fig.add_subplot(111)
		ax1.plot(saturation,krl,'--k',label='Liquid')
		ax1.plot(saturation,krg,'-k',label='Vapor')
		ax1.set_title("Corey RPF",fontsize=fontsize_)
		ax1.set_xlabel("Water saturation",fontsize=fontsize_)
		ax1.set_ylabel('Relative permeabilty',fontsize=fontsize_)
		ax1.set_ylim([0,1])
		ax1.set_xlim([0,1])
		ax1.legend(loc='lower left',frameon=False,fontsize=fontsize_)
		ax1.tick_params(axis='both', which='major', labelsize=fontsize_,pad=1)
		yticks = ax1.yaxis.get_major_ticks() 
		yticks[0].label1.set_visible(False)

		if show_fig:
			plt.show()

		if sav_fig:
			fig.savefig("../output/coreys_permeabilities.png", idp=300) 

def plot_one_drawdown_from_txt(well,depth, savefig = False):
	"""From the real drawndown data a plot is generated for a desired well

	Parameters
	----------
	well : str
	  Selected well
	depth : float
	  Meters above the see level of desire plot

	Returns
	-------
	plot
	  Pressure vs time
	  
	Attention
	---------
	The file  input/drawdown/{pozo}_DD.dat must exist

	Note
	----
	The depth must exists on the drawdown file

	Examples
	--------
	>>> plot_one_drawdown_from_txt('WELL-1',0)
	"""

	#Read file
	file="../input/drawdown/%s_DD.dat"%well
	data=pd.read_csv("../input/drawdown/%s_DD.dat"%well)
	fontsize_layout=8

	data_inj = pd.read_csv("../input/mh/filtered/total_inj.csv", usecols = ['date_time', 'steam', 'liquid'])
	data_inj['date_time'] = pd.to_datetime(data_inj['date_time'] , format="%Y-%m-%d")

	data_p = pd.read_csv("../input/mh/filtered/total_p.csv", usecols = ['date_time', 'steam', 'liquid'])
	data_p['date_time'] = pd.to_datetime(data_p['date_time'] , format="%Y-%m-%d")

	if len(data.loc[data['TVD']==depth]['datetime'])>1:

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		dates=list(map(dates_func,data.loc[data['TVD']==depth]['datetime'].values))

		#Plotting

		fig, ax = plt.subplots(figsize=(10,4))
		ln1 = ax.plot(dates,data.loc[data['TVD']==depth]['pressure'].values,linestyle='None',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=3,label='drawdown')
		ax.set_title("Drawdown at well: %s at %s masl"%(well,depth) ,fontsize=fontsize_layout)
		ax.set_xlabel("Time",fontsize = fontsize_layout)
		ax.set_ylabel('Pressure [bar]',fontsize = fontsize_layout)


		#Plotting formating
		#xlims=[min(dates)-timedelta(days=365),max(dates)+timedelta(days=365)]

		xlims=[min(data_inj['date_time']),max(data_inj['date_time'])]

		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.set_xlim(xlims)
		ax.xaxis.set_major_formatter(years_fmt)


		ax2 = ax.twinx()
		ln2 = ax2.plot(data_inj['date_time'],data_p['steam']+data_p['liquid']-data_inj['liquid'],linestyle='-',color='m',linewidth=1,ms=1,label='Net flow rate',alpha=0.15)
		ax2.set_ylim([0,1000])
		ax2.set_yticks([50,100,150,200,250,300])
		ax2.set_ylabel('Flow rate [kg/s]',fontsize = fontsize_layout)
		ax2.yaxis.set_label_coords(1.05,0.18)

		lns = ln1+ln2
		labs = [l.get_label() for l in lns]
		ax.legend(lns, labs, loc="upper right")

		#ax.xaxis.set_major_locator(years)
		#fig.autofmt_xdate()

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)
		if savefig:
			fig.savefig("../input/drawdown/images/%s_%.2f.png"%(well,depth), idp=300)
		plt.show()

	else:
		print("""Error message: there is no drawdown data at %s for the well %s"""%(depth,well))

	return None

def plot_one_cooling_from_txt(well,depth):
	"""From the real cooling data a plot is generated for a desired well

	Parameters
	----------
	well : str
	  Selected well
	depth : float
	  Meters above the see level of desire plot

	Returns
	-------
	plot
	  Pressure vs time
	  
	Attention
	---------
	The file  input/cooling/{pozo}_DD.dat must exist

	Note
	----
	The depth must exists on the cooling file

	Examples
	--------
	>>> plot_one_cooling_from_txt('WELL-1',0)
	"""

	#Read file
	file="../input/drawdown/%s_C.dat"%well
	data=pd.read_csv("../input/cooling/%s_C.dat"%well)
	data.loc[data['TVD']==depth]['datetime']
	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
	dates=list(map(dates_func,data.loc[data['TVD']==depth]['datetime'].values))

	fontsize_layout=8

	#Plotting

	if len(data.loc[data['TVD']==depth]['datetime'])>1:
		fig, ax = plt.subplots(figsize=(10,4))
		ax.plot(dates,data.loc[data['TVD']==depth]['temperature'].values,linestyle='None',color=formats.plot_conf_color['T'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=3,label='cooling')
		ax.set_title("Well: %s at %s masl"%(well,depth) ,fontsize=fontsize_layout)
		ax.set_xlabel("Time",fontsize = fontsize_layout)
		ax.set_ylabel('Temperature [$^\circ$C]',fontsize = fontsize_layout)

		#Plotting formating
		xlims=[min(dates)-timedelta(days=365),max(dates)+timedelta(days=365)]
		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.set_xlim(xlims)
		ax.xaxis.set_major_formatter(years_fmt)

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)
	else:
		sys.exit("""Error message: there is no cooling data at %s for the well %s"""%(depth,well))	

	return plt.show()

def plot_one_cooling_and_drawdown_from_txt(well,depth):
	"""From the real cooling and drawdown data a plot is generated for a desired well

	Parameters
	----------
	well : str
	  Selected well
	depth : float
	  Meters above the see level of desire plot

	Returns
	-------
	plot
	  Temperature (yaxis1), pressure (yaxis2) and time
	  
	Attention
	---------
	The file  input/cooling/{pozo}_DD.dat and  input/drawdown/{pozo}_DD.dat must exist

	Note
	----
	The depth must exists on the cooling and drawdown files

	Examples
	--------
	>>> plot_one_cooling_and_drawdown_from_txt('WELL-1',0)
	"""

	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")

	#Read file cooling
	data_c=pd.read_csv("../input/cooling/%s_C.dat"%well)
	dates_c=list(map(dates_func,data_c.loc[data_c['TVD']==depth]['datetime'].values))

	#Read file DRAWDOWN
	data_d=pd.read_csv("../input/drawdown/%s_DD.dat"%well)
	dates_d=list(map(dates_func,data_d.loc[data_d['TVD']==depth]['datetime'].values))
	if len(dates_d)==0:
		print("There are no values for this depth")
	else:
		#Plotting

		fig, ax = plt.subplots(figsize=(10,4))
		ax2 = ax.twinx()

		#Plotting drawdown
		ax.plot(dates_d,data_d.loc[data_d['TVD']==depth]['pressure'].values,linestyle='None',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=3,label='drawdown',alpha=0.75)
		ax.set_title("Well: %s at %s masl"%(well,depth) ,fontsize=8)
		ax.set_xlabel("Time",fontsize = 8)
		ax.set_ylabel('Pressure [bar]',fontsize = 8)

		#Plotting cooling
		ax2.plot(dates_c,data_c.loc[data_c['TVD']==depth]['temperature'].values,linestyle='None',color=formats.plot_conf_color['T'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=3,label='cooling',alpha=0.75)
		ax2.set_ylabel('Temperature [$^\circ$C]',fontsize = 8)


		#Plotting formating
		xlims=[min(dates_d)-timedelta(days=365),max(dates_d)+timedelta(days=365)]
		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.set_xlim(xlims)
		ax.xaxis.set_major_formatter(years_fmt)

		fig.legend(bbox_to_anchor=(0.3, 0.26))

		#ax.xaxis.set_major_locator(years)
		#fig.autofmt_xdate()

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)
		
		return plt.show()

def plot_one_mh_from_txt(well,savefig=False):
	"""Creates a plot using the flow and enthalpy measurements

	Parameters
	----------
	well : str
	  Selected well

	Returns
	-------
	plot
	  Enthalpy (yaxis1), flow (yaxis2) vs time 
	  
	Attention
	---------
	The file ../input/mh/{well}_mh.dat must exist


	Examples
	--------
	>>> plot_one_mh_from_txt('WELL-1')
	"""


	fontsize_ylabel=8
	fontsize_title=9

	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d_%H:%M:%S")

	#Read file cooling
	data=pd.read_csv("../input/mh/%s_mh.dat"%well)
	dates=list(map(dates_func,data['date_time'].values))
	max_liq=max(data['liquid'])
	max_st=max(data['steam'])
	data = data.replace(0,np.nan)

	#Quality
	data['quality']= data['steam']/(data['liquid']+data['steam'])
	q_max = max(data['quality'].fillna(0))


	#Setting plot
	gs = gridspec.GridSpec(4, 1)
	fig, ax = plt.subplots(figsize=(12,7))


	#Flow plot
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax=plt.subplot(gs[0,0])
	ln1=ax.plot(dates,data['steam'],linestyle='None',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam',alpha=0.75)
	ax.set_ylim([0,max(max_liq,max_st)])

	ax1b = ax.twinx()
	ln2=ax1b.plot(dates,data['liquid'],linestyle='None',color=formats.plot_conf_color['ml'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid',alpha=0.75)
	ax.set_ylabel('Flow s[kg/s]',fontsize = fontsize_ylabel)
	ax1b.set_ylabel('Flow l[kg/s]',fontsize = fontsize_ylabel)
	ax1b.set_ylim([0,max(max_liq,max_st)])

	# legend for flow
	lns = ln1+ln2
	labs = [l.get_label() for l in lns]
	ax.legend(lns, labs, loc="upper right")

	#Enthalpy plot
	ax2=plt.subplot(gs[1,0], sharex = ax)
	ax2.plot(dates,data['enthalpy'],linestyle='None',color=formats.plot_conf_color['h'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Enthalpy',alpha=0.75)
	ax2.legend(loc="upper right")
	ax2.set_ylabel('Enthalpy [kJ/kg]',fontsize = fontsize_ylabel)


	#WHPressure plot
	ax3=plt.subplot(gs[3,0], sharex = ax)
	ax3.plot(dates,data['WHPabs']+0.92,linestyle='None',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Pressure',alpha=0.75)
	ax3.legend(loc="upper right")
	ax3.set_ylabel('Pressure [bara]',fontsize = fontsize_ylabel)


	#Quality
	ax4=plt.subplot(gs[2,0], sharex = ax)
	ax4.plot(dates,data['quality'],linestyle='None',color=formats.plot_conf_color['SG'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Quality',alpha=0.75)
	ax4.legend(loc="upper right")
	ax4.set_ylim([0,q_max+0.05])
	ax4.set_ylabel('Quality',fontsize = fontsize_ylabel)

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	plt.setp(ax.get_xticklabels(), visible=False)
	plt.setp(ax2.get_xticklabels(), visible=False)
	plt.setp(ax4.get_xticklabels(), visible=False)

	ax.xaxis.set_major_formatter(years_fmt)
	ax2.xaxis.set_major_formatter(years_fmt)
	ax3.xaxis.set_major_formatter(years_fmt)
	ax4.xaxis.set_major_formatter(years_fmt)

	#plt.subplots_adjust(hspace=0.0)

	fig.suptitle('Production history %s'%well,fontsize=fontsize_title)

	if savefig:
		fig.savefig("../input/mh/images/%s_raw.png"%well, format='png',dpi=300) 

	plt.show()

def check_layers_and_feedzones(input_dictionary, show_fig,sav_fig):
	"""It return a plot with the well TVD and the stratigrafy units

	Parameters
	----------
	show_fig: bool
		If True shows the figure
	sav_fig: bool
		If True saves the figure on ../output/
	input_dictionary : dictionary
		Contains the layers information under the keyword 'LAYER' and 'z_ref'. It also needs to specify the input files path under the keyword 'source_txt'

	Returns
	-------
	plot
	  well names on horizontal axis and feedzone depth on vertical axis

	Examples
	--------
	>>> plot_vertical_layer_distribution(layers,z0_level,show_fig,sav_fig=True)

	"""

	color_dict={'UI':'indianred',
				'UII':'orange',
				'UIII':'lightgreen',
				'UIV':'violet'}

	type_dict={'OBS':'m',
				'REIN':'b',
				'AMBREI':'c',
				'PROD':'r',
				'ABANDON':'grey',
				'WAITING':'k'}

	font_title_size=12
	fontsizey_layers=8
	fontsize_label=8

	layers_info =  geometry.vertical_layers(input_dictionary)
	z0_level = input_dictionary['z_ref']
	source_txt = input_dictionary['source_txt']


	#Plot setting 
	fig = plt.figure(figsize=(20, 10), dpi=100)
	ax = fig.add_subplot(111)

	feedzones = pd.read_csv(source_txt+'well_feedzone_xyz.csv',delimiter=",")
	elevations = pd.read_csv(source_txt+'ubication.csv',delimiter=",")
	units = pd.read_csv(source_txt+'lithology_units.csv',delimiter=";")

	index2plot = []
	wells_ticks = []
	z_wells = []
	for index,row in feedzones.iterrows():
		index2plot.append(index*4)
		wells_ticks.append(row['well'])
		z_wells.append(row['z'])

		#Adding tubes representation
		try:
			tubes_data=pd.read_csv('../input/tubes/%s_tubes.dat'%row['well'])
			ax.plot(2*[index*4],[elevations.loc[elevations.well==row['well']]['masl'],geometry.MD_to_TVD(row['well'],tubes_data['tr_lisa_fin'])[2]],'-k',lw=0.75)
			ax.plot(2*[index*4],[geometry.MD_to_TVD(row['well'],tubes_data['tranurada_inicio'])[2],geometry.MD_to_TVD(row['well'],tubes_data['tranurada_final'])[2]] ,':k',lw=0.75)
			ax.plot(index*4,row['z'],'+',ms=3,color=type_dict[row['type']],label=row['type'])

			for kx, rowk in units.loc[units.WELL==row['well']].iterrows():
				ax.plot(2*[(index+0.1)*4],[geometry.MD_to_TVD(row['well'],rowk.FROM)[2],geometry.MD_to_TVD(row['well'],rowk.TO)[2]],'-',lw=2,color=color_dict[rowk.UNIDADES],label=rowk.UNIDADES)

		except np.core._exceptions.UFuncTypeError:
			pass


	handles, labels = plt.gca().get_legend_handles_labels()
	by_label = dict(zip(labels, handles))
	ax.legend(by_label.values(), by_label.keys())

	ax.set_xticks(index2plot)
	ax.set_xticklabels(wells_ticks,rotation=90)

	y_layer_plot = layers_info['top']
	x_layer_plot = [index]*len(layers_info['top'])

	ax.xaxis.tick_top()
	ax.tick_params(axis='x',which='both',labelsize=6)
	
	Depth_lims = [min(layers_info['bottom']),max(layers_info['top'])]

	#Setting vertical axis
	ax.set_ylim(Depth_lims)
	ax.set_ylabel('m.a.s.l.',fontsize = fontsizey_layers)
	ax.set_yticks(layers_info['top'], minor=False)
	
	ax.title.set_position([0.5,1.05])
	ax.xaxis.set_label_coords(0.5,1.15)
	ax.yaxis.set_label_coords(-0.05,0.5)
	ax.tick_params(axis='y', which='major', labelsize=fontsizey_layers,pad=1)

	#Set layers

	ax2 = ax.twinx()            
	ax2.set_yticks(layers_info['top'], minor=True)
	ax2.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.6)
	ax2.set_yticks(layers_info['middle'], minor=False)
	ax2.set_yticklabels(layers_info['name'],fontsize=fontsize_label)
	ax2.tick_params(axis='y',which='both',length=0)
	ax2.set_ylabel('Layer',fontsize = fontsizey_layers)
	ax2.yaxis.set_label_coords(1.05,0.5)
	ax2.set_ylim(ax.get_ylim())

	plt.tight_layout()

	if show_fig:
		plt.show()
	if sav_fig:
		fig.savefig("../output/vertical_distribution_wells.png", format='png',dpi=300) 

def plot_init_conditions(input_dictionary,m,b,use_boiling=True,use_equation=False):
	"""Creates a plot for the initial pressure and temperature values

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the keyword 'INCONS_PARAM' with the specified initial conditions, i.e.: 'INCONS_PARAM':{'To':30,'GRADTZ':0.08,'DEPTH_TO_SURF':100,'DELTAZ':20}

	Returns
	-------
	plot
	  Pressure vs depth and temperature vs depth
	  
	Examples
	--------
	>>> plot_init_conditions(input_dictionary)
	"""

	from scipy.stats import linregress

	#Plot configuration
	fontsizex = 4
	fontsize_axis = 4
	fontsize_tick = 5
	fontsize_legend = 2
	
	#T and P limits

	max_T=325
	max_P=400
	max_depth=-3500
	min_depth=1500


	T, P, depths = t2funcs.initial_conditions(input_dictionary,m,b,use_boiling,use_equation)

	fig = plt.figure(figsize=(8, 8), dpi=300)
	axT = fig.add_subplot(121)
	axP = fig.add_subplot(122)

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	cm = plt.get_cmap('brg')
	N=len(wells)
	cnt=0

	string_file="name,intercept,slope,r\n"

	src='../input/PT'
	src_files = os.listdir(src)
	slopes=[]
	intercepts=[]
	for well in wells:
		file_name = well+'_MDPT.dat'
		full_file_name=src+'/'+file_name
		if os.path.isfile(full_file_name):
			cnt+=1	
			well=file_name.split('_')[0]
			data=pd.read_csv(full_file_name,sep=',')
			data['TVD']=data.apply(lambda x: geometry.MD_to_TVD(well,x['MD'])[2],axis=1)
			ln1T=axT.plot(data['T'],data['TVD'],label=well,lw=0.5,alpha=0.75)
			ln1T[0].set_color(cm(cnt/N))
			ln1P = axP.plot(data['P'],data['TVD'],label=well,lw=0.5,alpha=0.75)
			slope, intercept, r, p, se = linregress(data[data.P > 5]['P'].tolist(), data[data.P > 5]['TVD'].tolist())
			if slope>-19:
				slopes.append(slope)
				intercepts.append(intercept)
				string_file+="%s,%.2f,%.2f,%.2f\n"%(well,intercept,m,r)

			ln1P[0].set_color(cm(cnt/N))

	string_file+="average_real,%.2f,%.2f,0.0\n"%(np.average(slopes),np.average(intercepts))


	ln1T = axT.plot(T,depths,linestyle='-',color=formats.plot_conf_color['T'][0],marker=formats.plot_conf_marker['current'][0],linewidth=0.5,ms=1,label='Initial T')

	ln1P = axP.plot(P,depths,linestyle='-',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['current'][0],linewidth=0.5,ms=1,label='Initial P')

	slope, intercept, r, p, se = linregress(P[30:-1],depths[30:-1])

	string_file += "conditions,%.2f,%.2f,%.2f\n"%(intercept,slope,r)

	if use_boiling:
		title_s="using BPD"
	elif use_equation:
		title_s="using equation"

	file_log=open('../output/initial_conditions/initial_conditions_%s.csv'%title_s,'w')
	file_log.write(string_file)
	file_log.close()

	fig.suptitle('Initial conditions/Well conditions %s'%title_s, fontsize=fontsizex)
	plt.rc('legend', fontsize=fontsize_legend)

	fontsize_label=7

	axT.xaxis.tick_top()
	axT.set_xlabel('Temperature [$^\circ$C]',fontsize=fontsize_axis)
	axT.xaxis.set_label_coords(0.5,1.08)
	axT.tick_params(axis='both', which='major', labelsize=fontsize_tick,pad=1)
	axT.set_ylabel('TVD [m]',fontsize = fontsize_tick)
	axT.tick_params(axis='y',which='major',length=1)
	axT.set_xlim([0,max_T])
	axT.set_ylim([max_depth,min_depth])
	axT.grid(color = 'grey', linestyle = '--', linewidth = 0.1, alpha=0.5)
	legend_T=axT.legend(loc=3,ncol=2,bbox_to_anchor=(0.05,0.0125))

	layers_info =  geometry.vertical_layers(input_dictionary)	
	ax2 = axT.twinx()            
	ax2.set_yticks(layers_info['top'], minor=True)
	ax2.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.6)
	ax2.set_yticks(layers_info['middle'], minor=False)
	ax2.set_yticklabels(layers_info['name'],fontsize=fontsize_label)
	ax2.tick_params(axis='y',which='both',length=0)
	ax2.set_ylabel('Layer',fontsize = fontsize_label)
	ax2.yaxis.set_label_coords(1.05,0.5)
	ax2.set_ylim(axT.get_ylim())

	axP.xaxis.tick_top()
	axP.set_xlabel('Pressure [bar]',fontsize=fontsize_axis)
	axP.xaxis.set_label_coords(0.5,1.08)
	axP.tick_params(axis='both', which='major', labelsize=fontsize_tick,pad=1)
	axP.set_ylabel('TVD [m]',fontsize = fontsize_tick)
	axP.tick_params(axis='y',which='major',length=1)
	axP.set_xlim([0,max_P])
	axP.set_ylim(max_depth,min_depth)
	axP.grid(color = 'grey', linestyle = '--', linewidth = 0.1, alpha=0.5)
	legend_P=axP.legend(loc=3,ncol=2,bbox_to_anchor=(0.05,0.0125))

	ax3 = axP.twinx()            
	ax3.set_yticks(layers_info['top'], minor=True)
	ax3.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.6)
	ax3.set_yticks(layers_info['middle'], minor=False)
	ax3.set_yticklabels(layers_info['name'],fontsize=fontsize_label)
	ax3.tick_params(axis='y',which='both',length=0)
	ax3.set_ylabel('Layer',fontsize = fontsize_label)
	ax3.yaxis.set_label_coords(1.05,0.5)
	ax3.set_ylim(axP.get_ylim())

	legend_P.get_frame().set_linewidth(0.25)
	for legend_handle in legend_P.legendHandles:
		legend_handle.set_markersize(1.5)
		legend_handle.set_linewidth(0.25)
	
	fig.savefig("../output/initial_conditions/%s.png"%title_s, format='png',dpi=300)

	plt.show()


#not documented

def plot_liquid_vs_WHP(well,savefig=False):
	"""Creates a plot using the flow and enthalpy measurements

	Parameters
	----------
	well : str
	  Selected well

	Returns
	-------
	plot
	  Enthalpy (yaxis1), flow (yaxis2) vs time 
	  
	Attention
	---------
	The file ../input/mh/{well}_mh.dat must exist


	Examples
	--------
	>>> plot_one_mh_from_txt('WELL-1')
	"""


	fontsize_ylabel=8
	fontsize_title=9

	#Read file cooling
	data=pd.read_csv("../input/mh/%s_mh.dat"%well)
	max_liq=max(data['liquid'])
	max_st=max(data['steam'])
	data = data.replace(0,np.nan)

	#Setting plot
	fig, ax = plt.subplots(figsize=(10,10))

	#Flow plot
	ax=plt.subplot(111)
	ln1=ax.plot(data['WHPabs']+0.92,data['liquid'],linestyle='None',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Pressure',alpha=0.75)

	ax.set_ylim([0,max(data['liquid'].fillna(0))])
	ax.set_xlim([0,max(data['WHPabs'].fillna(0))])
	ax.set_ylabel('Flow [kg/s]',fontsize = fontsize_ylabel)
	ax.set_xlabel('Pressure [bara]',fontsize = fontsize_ylabel)
	fig.suptitle('%s'%well,fontsize=fontsize_title)

	if savefig:
		fig.savefig("../input/mh/images/%s_injector.png"%well, format='png',dpi=300) 

	plt.show()

def plot_total_vs_WHP(well,savefig=False):
	"""Creates a plot using the flow and enthalpy measurements

	Parameters
	----------
	well : str
	  Selected well

	Returns
	-------
	plot
	  Enthalpy (yaxis1), flow (yaxis2) vs time 
	  
	Attention
	---------
	The file ../input/mh/{well}_mh.dat must exist


	Examples
	--------
	>>> plot_one_mh_from_txt('WELL-1')
	"""

	fontsize_ylabel=8
	fontsize_title=9

	#Read file cooling
	data=pd.read_csv("../input/mh/%s_mh.dat"%well)
	max_liq=max(data['liquid'])
	max_st=max(data['steam'])
	data = data.replace(0,np.nan)

	#Setting plot
	fig, ax = plt.subplots(figsize=(10,10))

	#Flow plot
	ax=plt.subplot(111)
	ln1=ax.plot(data['WHPabs']+0.92,data['liquid']+data['steam'],linestyle='None',color=formats.plot_conf_color['m'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Total',alpha=0.75)
	ln2=ax.plot(data['WHPabs']+0.92,data['steam'],linestyle='None',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam',alpha=0.75)
	ln3=ax.plot(data['WHPabs']+0.92,data['liquid'],linestyle='None',color=formats.plot_conf_color['ml'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid',alpha=0.75)


	lns = ln1+ln2+ln3
	labs = [l.get_label() for l in lns]
	ax.legend(lns, labs, loc="lower left")

	ax.set_ylim([0,max((data['liquid']+data['steam']).fillna(0))])
	ax.set_xlim([0,max(data['WHPabs'].fillna(0))])
	ax.set_ylabel('Flow [kg/s]',fontsize = fontsize_ylabel)
	ax.set_xlabel('Pressure [bara]',fontsize = fontsize_ylabel)
	fig.suptitle('%s'%well,fontsize=fontsize_title)

	if savefig:
		fig.savefig("../input/mh/images/%s_producer.png"%well, format='png',dpi=300) 

	plt.show()

def total_flow(wells, savefig = None, ffill = False):


	years = range(1990,2022,1)
	months = range(1,13)
	days = [7, 14, 21, 28]

	dates_x = []
	for year in years:
		for month in months:
			if month<10:
				month_s='0%s'%month
			else:
				month_s=month
			for day in days:
				if day<10:
					day_s='0%s'%day
				else:
					day_s=day
				dates_x.append("%s-%s-%s_00:00:00"%(year,month_s,day_s))

	data_week = pd.DataFrame(columns = ['date_time', 'steam', 'liquid'])
	data_week['date_time'] = dates_x
	data_week['date_time'] = pd.to_datetime(data_week['date_time'] , format="%Y-%m-%d_%H:%M:%S")


	fontsize_ylabel=8
	fontsize_title=9

	data_p = pd.DataFrame(columns = ['date_time', 'steam', 'liquid'])
	data_inj = pd.DataFrame(columns = ['date_time', 'steam', 'liquid'])

	data_p_r = pd.DataFrame(columns = ['date_time', 'steam', 'liquid'])
	data_inj_r = pd.DataFrame(columns = ['date_time', 'steam', 'liquid'])

	fig, ax = plt.subplots(figsize=(12,7))

	#Flow plot
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax = plt.subplot(111)

	#inspect = ['TR-5', 'TR-5A', 'TR-5B', 'TR-5C', 'TR-5D']
	#inspect = ['TR-18', 'TR-18A', 'TR-18B', 'TR-18C']
	#inspect = ['TR-2', 'TR-9']
	inspect = []

	for well in wells:
		
		data_x = pd.read_csv("../input/mh/%s_mh.dat"%well, usecols = ['date_time', 'steam', 'liquid'])
		data_x['date_time'] = pd.to_datetime(data_x['date_time'] , format="%Y-%m-%d_%H:%M:%S")
		
		data_i = pd.read_csv("../input/mh/filtered/%s_week_avg.csv"%well, usecols = ['date_time', 'steam', 'liquid'])
		data_i['date_time'] = pd.to_datetime(data_i['date_time'] , format="%Y-%m-%d %H:%M:%S")

		data_i.index = data_i['date_time']
		data_ii_inter = data_i

		if ffill:
			data_ix = data_x.copy()
			data_ix.index = data_ix['date_time']
			del data_ix['date_time']
			data_ii_inter_x = data_ix.resample('D').mean().ffill()
			data_ii_inter_x['date_time'] = data_ii_inter_x.index
		else:
			data_ii_inter_x = data_x

		if wells[well]['type'] == 'producer' and well in inspect:
			c = ax.plot(data_ii_inter['steam'].index,data_ii_inter['steam'],linestyle='-',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label="%s_avg"%well,alpha=0.5)
			ax.plot(data_x['date_time'],data_x['steam'],linestyle='-',color = c[0].get_color(),marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label="%s_real"%well,alpha=0.75)

		if wells[well]['type'] == 'producer':
			data_p = data_p.append(data_ii_inter, ignore_index = True)
			data_p_r = data_p_r.append(data_ii_inter_x, ignore_index = True)
		elif wells[well]['type'] == 'injector':
			data_inj = data_inj.append(data_ii_inter, ignore_index = True)
			data_inj_r = data_inj_r.append(data_ii_inter_x, ignore_index = True)


	data_p = data_p.groupby('date_time').sum()
	data_inj = data_inj.groupby('date_time').sum()

	data_p_r = data_p_r.groupby('date_time').sum()
	data_inj_r = data_inj_r.groupby('date_time').sum()

	ln1 = ax.plot(data_p['steam'].index,data_p['steam']+data_p['liquid'],linestyle='-',color=formats.plot_conf_color['m'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=4,label='Total',alpha=0.75)
	ln2 = ax.plot(data_p['steam'].index,data_p['steam'],linestyle='-',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=4,label='Steam',alpha=0.75)
	ln3 = ax.plot(data_p['liquid'].index,data_p['liquid'],linestyle='-',color=formats.plot_conf_color['ml'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=4,label='Liquid',alpha=0.75)
	ln4 = ax.plot(data_inj['liquid'].index,data_inj['liquid'],linestyle='--',color=formats.plot_conf_color['ml'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=4,label='Injection',alpha=0.75)

	ln6 = ax.plot(data_p_r['steam'].index,data_p_r['steam'],linestyle='-',color='y',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam real',alpha=0.5)
	ln7 = ax.plot(data_p_r['liquid'].index,data_p_r['liquid'],linestyle='-',color='m',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid real',alpha=0.5)

	#ln5 = ax.plot(data_inj['liquid'].index,data_p['steam']+data_p['liquid']-data_inj['liquid'],linestyle='-',color='k',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Net',alpha=0.75)


	data_inj.to_csv('../input/mh/filtered/total_inj.csv' , index = True)
	data_p.to_csv('../input/mh/filtered/total_p.csv' , index = True)

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')
	ax.xaxis.set_major_formatter(years_fmt)

	ax.legend(loc="upper left")
	ax.set_ylabel('Mass flow [kg/s]',fontsize = fontsize_ylabel)
	ax.set_xlabel('Time ',fontsize = fontsize_ylabel)
	ax.set_ylim([0,max(data_p['steam']+data_p['liquid'])+25])

	plt.show()

	if savefig:
		fig.savefig("../input/mh/images/total_flow.png", format='png',dpi=300) 

def resample(well, type_well, save_fig = True):

	#Reading files

	data_x = pd.read_csv("../input/mh/%s_mh.dat"%well, usecols = ['date_time', 'steam', 'liquid', 'WHPabs', 'enthalpy', 'status'])
	data_x['date_time'] = pd.to_datetime(data_x['date_time'] , format="%Y-%m-%d_%H:%M:%S")


	#Resampling the data for every day and filling values backwards
	data_ii = data_x.copy()
	data_ii.index = data_ii['date_time']
	del data_ii['date_time']

	def mode_IP(x):
		return x.mode()

	data_ii_inter = data_ii.resample('D').agg({'steam': 'mean', 'liquid': 'mean', 'WHPabs': 'mean', 'enthalpy': 'mean', 'status' :mode_IP }).ffill()
	#data_ii_inter = data_ii.resample('D').mean().ffill()
	data_ii_inter['date_time'] = data_ii_inter.index

	#Finding cummulative sum for raw data
	data_ii_inter.fillna(0, inplace = True)
	data_c_real = data_ii_inter.cumsum()

	print(data_ii_inter)

	#Generating initial and last values of each interval

	dates_x = []
	years = range(1990,2022,1)
	months = range(1,13)
	days =  [15] #[7, 14, 21, 28] #[8, 23]

	for year in years:
		for month in months:
			if month<10:
				month_s='0%s'%month
			else:
				month_s=month
			for day in days:
				if day<10:
					day_s='0%s'%day
				else:
					day_s=day
				dates_x.append("%s-%s-%s_00:00:00"%(year,month_s,day_s))

	data_week = pd.DataFrame(columns = ['date_time', 'steam', 'liquid', 'WHPabs', 'enthalpy', 'status'])
	data_week['date_time'] = dates_x
	data_week['date_time'] = pd.to_datetime(data_week['date_time'] , format="%Y-%m-%d_%H:%M:%S")
	data_week = data_week[data_week['date_time'] < '2021-08-17'] #The last value day with data


	#******* Approach one, simple average every 7 days *******

	data_f = pd.DataFrame(columns = ['date_time', 'steam', 'liquid', 'WHPabs', 'enthalpy', 'status'])

	data = data_ii_inter

	data.drop(['date_time'], axis=1 , inplace = True)

	data = data.rename_axis('date_time').reset_index()

	prev_type = data['status'][0]

	for index in data_week.index[0:-2]:
		mask = (data['date_time'] > data_week['date_time'][index]) & (data['date_time'] <= data_week['date_time'][index+1])

		avg_time = pd.DataFrame(data = [ ['X',data_week['date_time'][index]],['X',data_week['date_time'][index+1]] ], columns = ['d','time'])

		avg_time.time = pd.to_datetime(avg_time.time).values.astype(np.int64)

		avg_time = pd.DataFrame(pd.to_datetime(avg_time.groupby('d').mean().time))

		tmp = data.loc[mask]

		tmp.reset_index(inplace=True)

		no_data = False
		
		if tmp.empty and data_week['date_time'][index] < data['date_time'][0]:
			print("No data")
			no_data = True

		elif len(tmp) != 0:
			t1 = avg_time['time'][0]

			op_mode = tmp['status'].mode()[0]

			if len(op_mode) == 0:
				op_mode = prev_type

			prev_type = op_mode


			if t1 < tmp['date_time'][0]:
				t1 = tmp['date_time'][0]

			ml = tmp['liquid'].mean()
			data_i = {'date_time' : [t1],\
			          'liquid' : [ml],
			          'enthalpy':[tmp['enthalpy'].mean()],
					  'WHPabs':[tmp['WHPabs'].mean()],
					  'status': [op_mode]}

			if type_well == 'producer':
				ms = tmp['steam'].mean()
				steam_flow = {'steam' : [ms]}
			else:
				steam_flow = {'steam' : [0.0]}

			data_i.update(steam_flow)
		else:
			no_data = True

		if not no_data:
			df = pd.DataFrame(data_i)
			df['date_time'] = pd.to_datetime(df['date_time'] , format="%Y-%m-%d %H:%M:%S")
			data_f = data_f.append(df, ignore_index = True)

	data_f['date_time'] = pd.to_datetime(data_f['date_time'] , format="%Y-%m-%d_%H:%M:%S")
	data_f.index = data_f['date_time']
	del data_f['date_time']

	#Cummulative for values first approach 
	data_1 = data_f.resample('D').mean().ffill()
	data_1_c = data_1.cumsum()


	#******* Second approach, use cummulative values *******


	data_c = data_ii_inter.cumsum()
	
	data_f_i = pd.DataFrame(columns = ['date_time', 'steam', 'liquid', 'WHPabs', 'enthalpy', 'type'])
	

	for index in data_week.index[0:-2]:
		mask = (data_c.index > data_week['date_time'][index]) & (data_c.index <= data_week['date_time'][index+1])

		avg_time = pd.DataFrame(data = [ ['X',data_week['date_time'][index]],['X',data_week['date_time'][index+1]] ], columns = ['d','time'])
		avg_time.time = pd.to_datetime(avg_time.time).values.astype(np.int64)
		avg_time = pd.DataFrame(pd.to_datetime(avg_time.groupby('d').mean().time))

		tmp = data_c.loc[mask]
		tmp_st = data_c.loc[mask]

		tmp.reset_index(inplace=True)
		no_data = False

		if tmp.empty and data_week['date_time'][index] < data_c.index[0]:
			print("No data")
			no_data = True

		elif len(tmp) != 0:

			#dt = pd.Series(len(tmp)*np.array([24*3600]))

			tmp.drop(['status'], axis=1 , inplace = True)
			tmp_dt = tmp.diff()
			tmp_dt['type'] = tmp_st['status'].mode()

			t1 = avg_time['time'][0]
			if t1 < tmp['date_time'][0]:
				t1 = tmp['date_time'][0]


			ml = tmp_dt['liquid'].mean()
			h = tmp_dt['enthalpy'].mean()
			WHP = tmp_dt['WHPabs'].mean()

			data_i = {'date_time' : [t1],\
			          'liquid' : [ml],
			          'enthalpy':[h],
					  'WHPabs':[WHP],
					  'status': [op_mode]}

			if type_well == 'producer':
				ms = tmp_dt['steam'].mean()
				steam_flow = {'steam' : [ms]}
			else:
				steam_flow = {'steam' : [0.0]}

			data_i.update(steam_flow)
		
		else:
			no_data = True

		if not no_data:
			df = pd.DataFrame(data_i)
			df['date_time'] = pd.to_datetime(df['date_time'] , format="%Y-%m-%d %H:%M:%S")
			data_f_i = data_f_i.append(df, ignore_index = True)

	data_f_i['date_time'] = pd.to_datetime(data_f_i['date_time'] , format="%Y-%m-%d_%H:%M:%S")
	data_f_i.index = data_f_i['date_time']
	del data_f_i['date_time']
	
	#Cummulative for values second approach 
	data_2 = data_f_i.resample('D').mean().ffill()
	data_2_c = data_2.cumsum()


	data_f.to_csv('../input/mh/filtered/%s_week_avg.csv'%well, index = True)

	#Setting the plot
	figs = plt.figure(figsize=(12,7))
	fontsize_ylabel=8
	fontsize_title=9

	#Steam plot comparisson

	ax = figs.add_subplot(111)
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax.set_ylabel('Mass flow [kg/s]',fontsize = fontsize_ylabel)
	ax.set_xlabel('Time ',fontsize = fontsize_ylabel)
	ax.set_title('%s Steam comparisson'%well,fontsize=fontsize_title)

	ln1_s = ax.plot(data_x['date_time'],data_x['steam'],linestyle='-',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam raw data',alpha=0.75)
	ln2_s = ax.plot(data_ii_inter['steam'].index,data_ii_inter['steam'],linestyle='None',color='k',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam resample 1D',alpha=0.75)
	ln3_s = ax.plot(data_f['steam'].index,data_f['steam'],linestyle='None',color='m',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=4,label='Avg steam approach 1',alpha=0.75)
	ln4_s = ax.plot(data_f_i['steam'].index,data_f_i['steam'],linestyle='None',color='g',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=4,label='Avg steam approach 2',alpha=0.75)

	ax.legend(loc="upper left")

	#Liquid plot comparisson

	figl = plt.figure(figsize=(12,7))

	axl = figl.add_subplot(111)
	axl.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	axl.set_ylabel('Mass flow [kg/s]',fontsize = fontsize_ylabel)
	axl.set_xlabel('Time ',fontsize = fontsize_ylabel)
	axl.set_title('%s Liquid comparisson'%well,fontsize=fontsize_title)

	ln1_l = axl.plot(data_x['date_time'],data_x['liquid'],linestyle='-',color=formats.plot_conf_color['ml'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid raw data',alpha=0.75)
	ln2_l = axl.plot(data_ii_inter['liquid'].index,data_ii_inter['liquid'],linestyle='None',color='k',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid resample 1D',alpha=0.75)
	ln3_l = axl.plot(data_f['liquid'].index,data_f['liquid'],linestyle='None',color='m',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=2,label='Avg liquid approach 1',alpha=0.75)
	ln4_l = axl.plot(data_f_i['liquid'].index,data_f_i['liquid'],linestyle='None',color='g',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=2,label='Avg liquid approach 2',alpha=0.75)

	axl.legend(loc="upper left")

	#Steam cummulative comparisson
	
	fig_comp_s = plt.figure(figsize=(12,7))

	ax_cs = fig_comp_s.add_subplot(111)
	ax_cs.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax_cs.set_ylabel('Mass [kg]',fontsize = fontsize_ylabel)
	ax_cs.set_xlabel('Time ',fontsize = fontsize_ylabel)
	ax_cs.set_title('%s cummulative comparisson'%well,fontsize=fontsize_title)

	ln1_c = ax_cs.plot(data_c_real['date_time'].index,data_c_real['steam'],linestyle='-',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Real cummulative steam',alpha=0.75)
	ln2_c = ax_cs.plot(data_1_c['steam'].index,data_1_c['steam'],linestyle='None',color='k',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=2,label='Cummulative steam approach 1',alpha=0.75)
	ln3_c = ax_cs.plot(data_2_c['steam'].index,data_2_c['steam'],linestyle='None',color='m',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=2,label='Cummulative steam approach 2',alpha=0.75)

	ax_cs.legend(loc="upper left")


	#Liquid cummulative comparisson
	
	fig_comp_l = plt.figure(figsize=(12,7))

	ax_cl = fig_comp_l.add_subplot(111)
	ax_cl.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax_cl.set_ylabel('Mass [kg]',fontsize = fontsize_ylabel)
	ax_cl.set_xlabel('Time ',fontsize = fontsize_ylabel)
	ax_cl.set_title('%s cummulative comparisson'%well,fontsize=fontsize_title)

	ln1_c = ax_cl.plot(data_c_real['date_time'].index,data_c_real['liquid'],linestyle='-',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam C real',alpha=0.75)
	ln2_c = ax_cl.plot(data_1_c['liquid'].index,data_1_c['liquid'],linestyle='None',color='k',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Cummulative liquid approach 1',alpha=0.75)
	ln3_c = ax_cl.plot(data_2_c['liquid'].index,data_2_c['liquid'],linestyle='None',color='m',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Cummulative liquid approach 2',alpha=0.75)

	ax_cl.legend(loc="upper left")

	#Steam cummulative comparisson
	
	fig_comp_sp = plt.figure(figsize=(12,7))

	ax_csp = fig_comp_sp.add_subplot(111)
	ax_csp.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax_csp.set_ylabel('Percentage [%]',fontsize = fontsize_ylabel)
	ax_csp.set_xlabel('Time ',fontsize = fontsize_ylabel)
	ax_csp.set_title('%s cummulative difference'%well,fontsize=fontsize_title)

	del data_c_real['date_time']
	diff_1 = (data_1_c.merge(right=data_c_real, left_on='date_time', right_on='date_time', how='left').assign(steam_diff=lambda df: (df['steam_x'] - df['steam_y'])*100/df['steam_y'] ))
	diff_2 = (data_2_c.merge(right=data_c_real, left_on='date_time', right_on='date_time', how='left').assign(steam_diff=lambda df: (df['steam_x'] - df['steam_y'])*100/df['steam_y'] ))

	ln2_c = ax_csp.plot(diff_1['steam_diff'].index,diff_1['steam_diff'],linestyle='None',color='k',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Cummulative diff steam approach 1',alpha=0.75)
	ln3_c = ax_csp.plot(diff_2['steam_diff'].index,diff_2['steam_diff'],linestyle='None',color='m',marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Cummulative diff steam approach 2',alpha=0.75)

	ax_csp.legend(loc="lower right")

	#Histogram

	from scipy.stats import norm

	fig_ap=  plt.figure(figsize=(12,7))
	ax_ap1=fig_ap.add_subplot(121)
	ax_ap2=fig_ap.add_subplot(122)
	# An "interface" to matplotlib.axes.Axes.hist() method
	m_diff_1 = (data_1['steam']-data_ii_inter['steam'])
	m_diff_1.dropna(inplace = True)
	n, bins, patches = ax_ap1.hist(x=m_diff_1, bins = 80, density = True, rwidth=0.85)
	muT, stdT = norm.fit(m_diff_1)
	m_diff_1_x = np.linspace(min(m_diff_1), max(m_diff_1), 100)
	ax_ap1.plot(bins,norm.pdf(bins, muT, stdT),'--r')

	m_diff_2 = (data_2['steam']-data_ii_inter['steam']) 
	m_diff_2.dropna(inplace = True)
	n2, bins2, patches2 = ax_ap2.hist(x=m_diff_2, bins = 80, density = True, rwidth=0.85)
	muT2, stdT2 = norm.fit(m_diff_2)
	m_diff_2_x = np.linspace(min(m_diff_2), max(m_diff_2), 100)
	ax_ap2.plot(bins2,norm.pdf(bins2, muT2, stdT2),'--r')

	ax_ap1.set_xlabel(r'Diff [$\dot{m}$]')
	ax_ap1.set_ylabel('Probability')
	ax_ap1.set_title('Approach 1: ' + r'$\mu = '+'%.4f ,'%muT+r'\sigma$ = '+'%.4f'%stdT)

	ax_ap2.set_xlabel(r'Diff [$\dot{m}$]')
	ax_ap2.set_ylabel('Probability')
	ax_ap2.set_title('Approach 2: ' + r'$\mu = '+'%.4f ,'%muT2+r'\sigma$ = '+'%.4f'%stdT2)

	if save_fig:
		figs.savefig('../input/mh/filtered/images/steam/%s_steam.png'%well,dpi = 300)
		figl.savefig('../input/mh/filtered/images/liquid/%s_liquid.png'%well,dpi = 300)
		fig_comp_s.savefig('../input/mh/filtered/images/cummulative/%s_c_s.png'%well,dpi = 300)
		fig_comp_l.savefig('../input/mh/filtered/images/cummulative/%s_c_l.png'%well,dpi = 300)
		fig_comp_sp.savefig('../input/mh/filtered/images/diff/%s_porc_s.png'%well,dpi = 300)
		fig_ap.savefig('../input/mh/filtered/images/diff/%s_diff_histo.png'%well,dpi = 300)
		plt.close()
	else:
		plt.show()

def mh_duplicates(input_dictionary):

	db_path=input_dictionary['db_path']

	conn=sqlite3.connect(db_path)

	types='WELLS'
	wells=[]
	try:
		for well in input_dictionary[types]:
			wells.append(well)
	except KeyError:
			pass

	#Setting the plot
	fig= plt.figure(figsize=(12,7))

	ax = fig.add_subplot(111)
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')

	colormap = plt.cm.nipy_spectral
	colors = [colormap(i) for i in np.linspace(0, 1,len(wells))]
	ax.set_prop_cycle('color', colors)


	for i, well in enumerate(sorted(wells)):
		data=pd.read_sql_query("SELECT type,date_time,steam_flow+liquid_flow as m_total,flowing_enthalpy,well_head_pressure FROM mh_f WHERE well='%s';"%well,conn)
		data['date_time'] = pd.to_datetime(data['date_time'] , format="%Y-%m-%d %H:%M:%S")

		i_s = [i for n in range(len(data['m_total']))]

		if well == 'TR-9':
			for  index,row in data.iterrows():
				ax.plot([row['date_time'],row['date_time']],[0,37], '-k', lw = 0.15, alpha = 0.5)

		ax.plot(data['date_time'],i_s, marker = 'o', ms = 2, linestyle = 'None' ,label = well)

	ax.legend(loc = 'upper right', fontsize = 6)
	plt.show()


def field(input_dictionary):
	input_file = "../input/field_data.csv"
	if os.path.isfile(input_file):
		data=pd.read_csv(input_file)

		data.dropna(inplace = True)

		data['fecha'] = pd.to_datetime(data['fecha'] , format="%Y%m%d")
		data=data.set_index(['fecha'])
		data.index = pd.to_datetime(data.index)

		fig=plt.figure()

		ax=fig.add_subplot(111)

		data['extraction'] = data['agua']+data['vapor']
		data['net'] = data['agua']+data['vapor']-data['inyeccion']

		extraction = data['extraction'].rolling(window = 180).mean()
		injection = data['inyeccion'].rolling(window = 180).mean()
		net = data['net'].rolling(window = 180).mean()


		#ax.plot(extraction, lw = 1, label = 'Total extraction')
		#ax.plot(injection, lw = 1, label = 'Injection')
		ax.plot(net, lw = 1, label = 'Net extraction', color = '#4575b4')
		ax.set_ylim([0, 300])
		ax.set_ylabel('Mass flow rate [kg/s]')
		ax.set_xlabel('Year')

		axt = ax.twinx()
		axt.set_ylabel('Pressure [bar]')
		axt.set_ylim([-max(data['prs1']), 1])

		drawdown = data.loc[data['prs1'] > 0,['prs1']]
		drawdown = drawdown['prs1'].resample('60D').mean()
		drawdown = pd.DataFrame({'dates':drawdown.index, 'prs1':drawdown.values})

		#smooth = data.loc[data['prs1'] > 0,['prs1']]
		#df_loess_5 = pd.DataFrame(lowess(smooth['prs1'],  np.arange(len(smooth['prs1'])), frac=0.05)[:, 1], index=smooth.index, columns=['prs1'])
		#axt.plot(df_loess_5,linestyle = '-', marker = 'o', ms= 2)

		axt.plot(drawdown['dates'], drawdown['prs1'] - drawdown['prs1'].iloc[0], linestyle = 'None', marker = 'o', ms= 2.5, markerfacecolor='none', color='#d73027')
		
		plt.legend([ax.get_lines()[0],axt.get_lines()[0]],\
				                   ['Net flow rate extraction ','Pressure drawdown'],\
				                    loc=1, fancybox=True, shadow=True)

		plt.savefig('../output/net_flow_vs_pressure_dw.png', dpi = 600)

		plt.show()


def enthalpies_field(input_dictionary):

	input_file_1 = "../input/mh/unit12_mh.csv"
	input_file_2 = "../input/mh/unit3_17_mh.csv"
	input_file_3 = "../input/mh/unit3_18_mh.csv"

	if os.path.isfile(input_file_1) and os.path.isfile(input_file_2):

		data_12=pd.read_csv(input_file_1)
		data_12.dropna(inplace = True)
		data_12['date_time'] = pd.to_datetime(data_12['date_time'] , format="%Y-%m-%d")
		data_12=data_12.set_index(['date_time'])
		data_12.index = pd.to_datetime(data_12.index)

		h12 = data_12.loc[data_12['h'] > 0,['h','m']]
		h12_out = h12['h'].resample('120D').mean()
		h12_out_m = h12['m'].resample('120D').mean()
		

		data_3_17=pd.read_csv(input_file_2)
		data_3_17.dropna(inplace = True)
		data_3_17['date_time'] = pd.to_datetime(data_3_17['date_time'] , format="%Y-%m-%d")
		data_3_17=data_3_17.set_index(['date_time'])
		data_3_17.index = pd.to_datetime(data_3_17.index)

		h3_17 = data_3_17.loc[data_3_17['h'] > 0,['h','m']]
		h3_17_out = h3_17['h'].resample('120D').mean()
		h3_17_out_m = h3_17['m'].resample('120D').mean()

		data_3_18=pd.read_csv(input_file_3)
		data_3_18.dropna(inplace = True)
		data_3_18['date_time'] = pd.to_datetime(data_3_18['date_time'] , format="%Y-%m-%d")
		data_3_18=data_3_18.set_index(['date_time'])
		data_3_18.index = pd.to_datetime(data_3_18.index)

		h3_18 = data_3_18.loc[data_3_18['h'] > 0,['h','m']]
		h3_18_out = h3_18['h'].resample('120D').mean()
		h3_18_out_m = h3_18['m'].resample('120D').mean()


		fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, sharey=False)

		ax1.plot(h12_out, lw = 1, linestyle = 'None', marker = 'o', ms= 2.5, markerfacecolor='none', color='#4575b4', label = 'Center')
		ax1.plot(h3_17_out, lw = 1, linestyle = 'None', marker = 'o', ms= 2.5, markerfacecolor='none', color='#fc8d59', label = 'South 17s')
		ax1.plot(h3_18_out, lw = 1, linestyle = 'None', marker = 'o', ms= 2.5, markerfacecolor='none', color='#d73027', label = 'South 18s')

		ax2.fill_between(h12_out_m.index, h12_out_m.values, alpha=0.6, lw= 3, color = '#4575b4',  edgecolor = '#4575b4')
		ax2.fill_between(h3_17_out_m.index,h3_17_out_m.values, alpha=0.6, lw=3, color = '#fc8d59', edgecolor = '#fc8d59')
		ax2.fill_between(h3_18_out_m.index,h3_18_out_m.values, alpha=0.6, lw = 3, color = '#d73027', edgecolor = '#d73027')


		ax1.set_ylim([1000, 2000])
		ax1.set_ylabel('Enthalpy [kJ/kg]')
		ax2.set_ylabel('Mass flow rate [kg/s]')
		ax2.set_xlabel('Year')
		xlims=[min(data_12.index),max(h12_out_m.index)]
		ax2.set_xlim(xlims)
		ax2.set_ylim([0,max(h12_out_m)])
		
		ax1.legend([ax1.get_lines()[0],ax1.get_lines()[1],ax1.get_lines()[2]],\
				                   ['Center',"South TR-17's","South TR-18's"],\
				                    loc=2, fancybox=True, shadow=True)

		plt.savefig('../output/enthalpies_on_diff_areas.png', dpi = 600)

		plt.show()
		