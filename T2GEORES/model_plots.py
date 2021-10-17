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

def plot_one_drawdown_from_txt(well,depth):
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

	if len(data.loc[data['TVD']==depth]['datetime'])>1:

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		dates=list(map(dates_func,data.loc[data['TVD']==depth]['datetime'].values))

		#Plotting

		fig, ax = plt.subplots(figsize=(10,4))
		ax.plot(dates,data.loc[data['TVD']==depth]['pressure'].values,linestyle='None',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=3,label='drawdown')
		ax.set_title("Drawdown at well: %s at %s masl"%(well,depth) ,fontsize=fontsize_layout)
		ax.set_xlabel("Time",fontsize = fontsize_layout)
		ax.set_ylabel('Pressure [bar]',fontsize = fontsize_layout)


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
	
	else:
		sys.exit("""Error message: there is no drawdown data at %s for the well %s"""%(depth,well))
	return plt.show()

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

def plot_one_mh_from_txt(well):
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

	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")

	#Read file cooling
	data=pd.read_csv("../input/mh/%s_mh.dat"%well)
	dates=list(map(dates_func,data['date-time'].values))
	data = data.replace(0,np.nan)


	#Setting plot
	gs = gridspec.GridSpec(3, 1)
	fig, ax = plt.subplots(figsize=(10,4))


	#Flow plot
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')
	ax=plt.subplot(gs[0,0])
	ln1=ax.plot(dates,data['steam'],linestyle='-',color=formats.plot_conf_color['ms'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam',alpha=0.75)

	ax1b = ax.twinx()
	ln2=ax1b.plot(dates,data['liquid'],linestyle='-',color=formats.plot_conf_color['ml'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid',alpha=0.75)
	ax.set_ylabel('Flow s[kg/s]',fontsize = fontsize_ylabel)
	ax1b.set_ylabel('Flow l[kg/s]',fontsize = fontsize_ylabel)
	
	# legend for flow
	lns = ln1+ln2
	labs = [l.get_label() for l in lns]
	ax.legend(lns, labs, loc="upper right")

	#Enthalpy plot
	ax2=plt.subplot(gs[1,0])
	ax2.plot(dates,data['enthalpy'],linestyle='-',color=formats.plot_conf_color['h'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Enthalpy',alpha=0.75)
	ax2.legend(loc="upper right")
	ax2.set_ylabel('Enthalpy [kJ/kg]',fontsize = fontsize_ylabel)


	#WHPressure plot
	ax3=plt.subplot(gs[2,0])
	ax3.plot(dates,data['WHPabs'],linestyle='-',color=formats.plot_conf_color['P'][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Pressure',alpha=0.75)
	ax3.legend(loc="upper right")
	ax3.set_ylabel('Pressure [bara]',fontsize = fontsize_ylabel)

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	plt.setp(ax.get_xticklabels(), visible=False)
	plt.setp(ax2.get_xticklabels(), visible=False)

	ax.xaxis.set_major_formatter(years_fmt)
	ax2.xaxis.set_major_formatter(years_fmt)
	ax3.xaxis.set_major_formatter(years_fmt)

	fig.suptitle('Production history of well %s'%well,fontsize=fontsize_title)

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
	fontsize_tick = 3
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

	legend_P.get_frame().set_linewidth(0.25)
	for legend_handle in legend_P.legendHandles:
		legend_handle._legmarker.set_markersize(1.5)
		legend_handle._legmarker.set_linewidth(0.25)
	
	fig.savefig("../output/initial_conditions/%s.png"%title_s, format='png',dpi=300)

	plt.show()