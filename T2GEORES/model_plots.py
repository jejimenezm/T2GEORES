import  geometry as geometry
from model_conf import input_data
from formats import plot_conf_color,plot_conf_marker,formats_t2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import sys
import matplotlib.gridspec as gridspec
from iapws import IAPWS97
import t2geores_functions as t2funcs


def plot_vertical_layer_distribution(show_fig,sav_fig):
	"""Regresa informacion relacionada a las capas

	Parameters
	----------
	layers : dictionary
	  Diccionario generado en model_conf
	z0_level : int
	  Elevacion de referencia de model_conf
	show_fig: bool
	  Muestra figura
	sav_fig: bool
	  Guarda figura

	Other Parameters
	----------------
	int
	  font_title_size: tamanio de letra de titulo
	int
	  fontsizey_layers: Tamanio de letra de etiqueta vertical [m.a.s.l.]
	int
	  fontsize_label: Tamanio de letra de etiqueta vertical [layer]

	Examples
	--------
	>>> plot_vertical_layer_distribution(layers,z0_level,show_fig=True,sav_fig=False)

	"""

	font_title_size=12
	fontsizey_layers=10
	fontsize_label=8

	layers_info=geometry.vertical_layers(input_data['LAYERS'],input_data['z_ref'])

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
		fig.savefig("../report/images/vertical_distribution.png", format='png')

#plot_vertical_layer_distribution(show_fig=True,sav_fig=False)

def permeability_plot(IRP,slr,sgr,show_fig,sav_fig):
	"""Genera imagen de distribucion de permeabilidades relativas. La imagen es almacenada en formato .svg en la direccion ../report/images/coreys_permeabilities.svg

	Parameters
	----------
	show_fig: bool
	  Muestra figura
	sav_fig: bool
	  Guarda figura
	slr: float
	  Saturacion de liquido, tomado de model_conf
	sgr: float
	  Saturacion de gas, tomado de model_conf
	IRP: int
	  Tipo de distribucion de permeabilidades relativas, actualmente solo 'corey'

	Examples
	--------
	>>> permeability_plot(IRP,slr,sgr,show_fig,sav_fig)
	"""

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
			fig.savefig("../report/images/coreys_permeabilities.svg", format='svg') 

#permeability_plot(input_data['RPCAP']['IRP'],input_data['RPCAP']['RP1'],input_data['RPCAP']['RP2'],show_fig=True,sav_fig=False)

def plot_one_drawdown_from_txt(well,depth):
	"""Genera una grafica utilizando la informacion almacenada en ../input/drawdown para el pozo solicitado

	Parameters
	----------
	well : str
	  Pozo seleccionado
	depth : float
	  Profundidad vertical de grafico solicitado

	Returns
	-------
	graph
	  Presion vs tiempo para una profundidad especifica
	  
	Attention
	---------
	El archivo input/drawdown/{pozo}_DD.dat debe existir

	Note
	----
	La profundidad seleccionada debe estar en registrada en el archivo .dat

	Examples
	--------
	>>> plot_one_drawdown_from_txt('AH-34',0)
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
		ax.plot(dates,data.loc[data['TVD']==depth]['pressure'].values,linestyle='None',color=plot_conf_color['P'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=3,label='drawdown')
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

#plot_one_drawdown_from_txt('AH-34',0)

def plot_one_cooling_from_txt(well,depth):
	"""Genera una grafica utilizando la informacion almacenada en ../input/cooling para el pozo solicitado

	Parameters
	----------
	well : str
	  Pozo seleccionado
	depth : float
	  Profundidad de grafico solicitado

	Returns
	-------
	graph
	  Temperatura vs tiempo para una profundidad especifica
	  
	Attention
	---------
	El archivo input/cooling/{pozo}_C.dat debe existir

	Note
	----
	La profundidad seleccionada debe estar en registrada en el archivo .dat

	Examples
	--------
	>>> plot_one_cooling_from_txt('AH-34',0)
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
		ax.plot(dates,data.loc[data['TVD']==depth]['temperature'].values,linestyle='None',color=plot_conf_color['T'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=3,label='cooling')
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

#plot_one_cooling_from_txt('AH-34',0)

def plot_one_cooling_and_drawdown_from_txt(well,depth):
	"""Genera una grafica utilizando la informacion almacenada en ../input/cooling y ../input/cooling para el pozo solicitado

	Parameters
	----------
	well : str
	  Pozo seleccionado
	depth : float
	  Profundidad de grafico solicitado

	Returns
	-------
	graph
	  Temperatura (eje1), presion (eje2) vs tiempo para una profundidad especifica
	  
	Attention
	---------
	El archivo ../input/drawdown/{pozo}_DD.dat e input/cooling/{pozo}_C.dat debe existir

	Note
	----
	La profundidad seleccionada debe estar en registrada en el archivo .dat

	Examples
	--------
	>>> plot_one_cooling_and_drawdown_from_txt('AH-34',0)
	"""
	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")

	#Read file cooling
	data_c=pd.read_csv("../input/cooling/%s_C.dat"%well)
	dates_c=list(map(dates_func,data_c.loc[data_c['TVD']==depth]['datetime'].values))

	#Read file DRAWDOWN
	data_d=pd.read_csv("../input/drawdown/%s_DD.dat"%well)
	dates_d=list(map(dates_func,data_d.loc[data_d['TVD']==depth]['datetime'].values))
	if len(dates_d)==0:
		#print("There is not values for this depth")
		print("There is not values for this depth")
	else:
		#Plotting

		fig, ax = plt.subplots(figsize=(10,4))
		ax2 = ax.twinx()

		#Plotting drawdown
		ax.plot(dates_d,data_d.loc[data_d['TVD']==depth]['pressure'].values,linestyle='None',color=plot_conf_color['P'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=3,label='drawdown',alpha=0.75)
		ax.set_title("Well: %s at %s masl"%(well,depth) ,fontsize=8)
		ax.set_xlabel("Time",fontsize = 8)
		ax.set_ylabel('Pressure [bar]',fontsize = 8)

		#Plotting cooling
		ax2.plot(dates_c,data_c.loc[data_c['TVD']==depth]['temperature'].values,linestyle='None',color=plot_conf_color['T'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=3,label='cooling',alpha=0.75)
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

#plot_one_cooling_and_drawdown_from_txt('AH-34',0)

def plot_one_mh_from_txt(well):
	"""Genera una grafica utilizando la informacion almacenada en ../input/mh

	Parameters
	----------
	well : str
	  Pozo seleccionado

	Returns
	-------
	graph
	  Entalpia (eje1), flujo (eje2) vs tiempo 
	  
	Attention
	---------
	El archivo ../input/mh/{pozo}_mh.dat debe existir


	Examples
	--------
	>>> plot_one_mh_from_txt('AH-16A')
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
	ln1=ax.plot(dates,data['steam'],linestyle='-',color=plot_conf_color['ms'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Steam',alpha=0.75)

	ax1b = ax.twinx()
	ln2=ax1b.plot(dates,data['liquid'],linestyle='-',color=plot_conf_color['ml'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Liquid',alpha=0.75)
	ax.set_ylabel('Flow s[kg/s]',fontsize = fontsize_ylabel)
	ax1b.set_ylabel('Flow l[kg/s]',fontsize = fontsize_ylabel)
	
	# legend for flow
	lns = ln1+ln2
	labs = [l.get_label() for l in lns]
	ax.legend(lns, labs, loc="upper right")

	#Enthalpy plot
	ax2=plt.subplot(gs[1,0])
	ax2.plot(dates,data['enthalpy'],linestyle='-',color=plot_conf_color['h'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Enthalpy',alpha=0.75)
	ax2.legend(loc="upper right")
	ax2.set_ylabel('Enthalpy [kJ/kg]',fontsize = fontsize_ylabel)


	#WHPressure plot
	ax3=plt.subplot(gs[2,0])
	ax3.plot(dates,data['WHPabs'],linestyle='-',color=plot_conf_color['P'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Pressure',alpha=0.75)
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

#plot_one_mh_from_txt('AH-16A')

def check_layers_and_feedzones(show_fig,sav_fig,source_txt = '../input/'):
	"""Regresa informacion relacionada a las capas

	Parameters
	----------
	show_fig: bool
	  Muestra figura
	sav_fig: bool
	  Guarda figura
	source_txt: str
	  Indica el directorio donde se encuentran los archivos de entrada

	Other Parameters
	----------------
	int
	  font_title_size: tamanio de letra de titulo
	int
	  fontsizey_layers: Tamanio de letra de etiqueta vertical [m.a.s.l.]
	int
	  fontsize_label: Tamanio de letra de etiqueta vertical [layer]

	Examples
	--------
	>>> plot_vertical_layer_distribution(layers,z0_level,show_fig,sav_fig=True)

	"""

	font_title_size=12
	fontsizey_layers=8
	fontsize_label=8

	layers_info=geometry.vertical_layers(input_data['LAYERS'],input_data['z_ref'])


	#Plot setting 
	fig=plt.figure(figsize=(20, 10), dpi=100)
	ax=fig.add_subplot(111)

	feedzones=pd.read_csv(source_txt+'well_feedzone_xyz.csv',delimiter=",")

	index2plot=[]
	wells_ticks=[]
	z_wells=[]
	for index,row in feedzones.iterrows():
		index2plot.append(index*4)
		wells_ticks.append(row['well'])
		z_wells.append(row['z'])
		ax.plot(5*[index*4],np.linspace(z0_level,row['z'],5),'-k',lw=1,alpha=0.5)
		#ax.text(index*4,row['z'],row['well'],fontsize=6)
	
	#Set feedzones position 

	ax.plot(index2plot,z_wells,'ok',ms=2)

	ax.set_xticks(index2plot)
	ax.set_xticklabels(wells_ticks,rotation=90)

	y_layer_plot=layers_info['top']
	x_layer_plot=[index]*len(layers_info['top'])

	ax.xaxis.tick_top()
	ax.tick_params(axis='x',which='both',labelsize=6)
	
	Depth_lims=[min(layers_info['bottom']),max(layers_info['top'])]

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
		fig.savefig("../report/images/vertical_distribution_wells.png", format='png') 

#check_layers_and_feedzones(show_fig=True,sav_fig=False)

def plot_init_conditions():

	T, P, depths =t2funcs.initial_conditions()

	fig= plt.figure(figsize=(8, 8), dpi=300)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	ln1T=axT.plot(T,depths,linestyle='-',color=plot_conf_color['T'][0],marker=plot_conf_marker['current'][0],linewidth=0.5,ms=1)

	ln1P=axP.plot(P,depths,linestyle='-',color=plot_conf_color['P'][0],marker=plot_conf_marker['current'][0],linewidth=0.5,ms=1)

	#Plot configuration

	fontsizex=8
	fontsize_axis=4
	fontsize_tick=3
	fontsize_legend=2

	fig.suptitle('Initial conditions', fontsize=fontsizex)

	axT.xaxis.tick_top()
	axT.set_xlabel('Temperature [$^\circ$C]',fontsize=fontsize_axis)
	axT.xaxis.set_label_coords(0.5,1.08)
	axT.tick_params(axis='both', which='major', labelsize=fontsize_tick,pad=1)
	axT.set_ylabel('TVD [m]',fontsize = fontsize_tick)
	axT.tick_params(axis='y',which='major',length=1)
	axT.set_xlim([0,max(T)])
	axT.set_ylim([min(depths),max(depths)])

	axP.xaxis.tick_top()
	axP.set_xlabel('Pressure [bar]',fontsize=fontsize_axis)
	axP.xaxis.set_label_coords(0.5,1.08)
	axP.tick_params(axis='both', which='major', labelsize=fontsize_tick,pad=1)
	axP.set_ylabel('TVD [m]',fontsize = fontsize_tick)
	axP.tick_params(axis='y',which='major',length=1)
	axP.set_xlim([0,max(P)])
	axP.set_ylim([min(depths),max(depths)])

	plt.show()

#plot_init_conditions()