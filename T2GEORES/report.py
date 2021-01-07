import sys
import sqlite3
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os
import math
import matplotlib.gridspec as gridspec
from scipy.interpolate import griddata
import json
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.tri as mtri
import matplotlib.dates as mdates
import subprocess
from scipy import interpolate
from iapws import IAPWS97
import writer as t2w
from formats import formats_t2
import geometry as geomtr
from formats import plot_conf_color,plot_conf_marker

#It is a must to change the way a json is loaded

def plot_compare_one(well,savefig, no_real_data, data, TVD_elem, TVD_elem_top,axT,axP,PT_real_dictionary,layer_bottom,limit_layer,input_dictionary,label=None,def_colors=True):
	"""It generates two plots, they compare real downhole temperature and pressure measurements with model output 

	Parameters
	----------
	well : str
	  Selected well
	savefig : bool
	  If true the plot is saved on ../output/PT/images/logging/
	PT_real_dictionary : dictionary
	  Contains real  measurements on temperature, pressure and measure depth
	no_real_data : bool
	  If True, no real measurements are provides
	data : pandas dataframe
	  Contains model output information for each element assigned to a well
	TVD_elem : array
	  Contains the masl data at the middle for each element assigned to a well
	TVD_elem_top : array
	  Contains the masl data at the top  for each element assigned to a well
	axT : matplotlib_axis
	  Framework where temperature data is plotted
	axP : matplotlib_axis
	  Framework where temperature data is plotted
	layer_bottom : array
	  Contains the masl data at the bottom for each element assigned to a well
	limit_layer : str
	  Layer correlative at which plotting stops
	input_dictionary: dictionary
	  Contains the information of the top level of the mesh on under the key 'z_ref'
	label : str
	  Contains the legend of the plotted line
	def_colors : True
	  If True uses the colors defined on formats

	Returns
	-------
	image
		PT_{well}.png: on the path../output/PT/images/logging
	matplotlib_axis
	    axT: contains real and simulated downhole temperature data
	matplotlib_axis
	    axP: contains real and simulated downhole pressure data

	Note
	----
	It is used in combination of the function plot_compare_one_data

	"""

	fontsize_plot=8
	fontsize_layer=6

	z_ref=input_dictionary['z_ref']

	#Define plot

	if not no_real_data:

		#Plotting real data

		ln1T=axT.plot(PT_real_dictionary['var_T'],PT_real_dictionary['z_T'],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')

		ln1P=axP.plot(PT_real_dictionary['var_P'],PT_real_dictionary['z_P'],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')

		lnsT = ln1T

		lnsP = ln1P

	#Plotting the calculated data

	ln2T=axT.plot(data['T'],TVD_elem,linestyle='None',marker=plot_conf_marker['current'][0],label='Calculated %s'%label)

	ln2P=axP.plot(data['P']/1E5,TVD_elem,linestyle='None',marker=plot_conf_marker['current'][0],label='Calculated %s'%label)

	if def_colors:
		color_real_T=plot_conf_color['T'][0]
		color_real_P=plot_conf_color['P'][0]

		ln1T.set_color(color_real_T)
		ln2T.set_color(color_real_T)

		ln1P.set_color(color_real_P)
		ln2P.set_color(color_real_P)

	axT.set_ylim([layer_bottom[limit_layer],z_ref])

	axP.set_ylim([layer_bottom[limit_layer],z_ref])

	#Preparing the layer axis side for pressure

	ax2P = axP.twinx()

	ax2P.set_yticks(TVD_elem_top,minor=True)

	ax2P.set_yticks(TVD_elem,minor=False)

	ax2P.tick_params(axis='y',which='major',length=0)

	ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

	ax2P.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

	ax2P.set_ylim(axP.get_ylim())

	#Preparing the layer axis side for temperature

	ax2T = axT.twinx()

	ax2T.set_yticks(TVD_elem_top,minor=True)

	ax2T.set_yticks(TVD_elem,minor=False)
	
	ax2T.tick_params(axis='y',which='major',length=0)

	ax2T.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

	ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

	ax2T.set_ylim(axT.get_ylim())

	#Preparing the legends on temperature side
	if no_real_data:
		lnsT=ln2T
	else:
		lnsT+=ln2T

	labsT = [l.get_label() for l in lnsT]

	#axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsize_plot)

	axT.legend(loc='upper right',fontsize=fontsize_plot)

	axT.set_xlabel('Temperature [$^\circ$C]',fontsize=fontsize_plot)

	axT.xaxis.set_label_coords(0.5,1.05)

	axT.xaxis.tick_top()

	axT.set_ylabel('m.a.s.l.',fontsize = fontsize_plot)

	axT.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	#Preparing the legends on pressure side
	if no_real_data:
		lnsP=ln2P
	else:
		lnsP+=ln2P

	labsP = [l.get_label() for l in lnsP]

	#axP.legend(lnsP, labsP, loc='upper right', fontsize=fontsize_plot)
	
	axP.legend(loc='upper right', fontsize=fontsize_plot)

	axP.set_xlabel('Pressure [bar]',fontsize=fontsize_plot)

	axP.xaxis.set_label_coords(0.5,1.05)

	axP.xaxis.tick_top()

	axP.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	#Title for both plots

	#plt.subplots_adjust(top=0.92)

	if savefig:
		fig.savefig('../output/PT/images/logging/PT_%s.png'%well)

def plot_compare_one_data(well,input_dictionary,inpath="../output/PT/txt"):
	"""Compiles real and output for temperature and pressure data 

	Parameters
	----------	  
	well : str
	  Selected well
	input_dictionary : dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path'
	inpath : str
	  Constains path for input files. Default value is "../output/PT/txt"

	Returns
	-------
	PT_real_dictionary : dictionary
	  Contains real  measurements on temperature, pressure and measure depth
	no_real_data : bool
	  If True, no real measurements are provides
	data : pandas dataframe
	  Contains model output information for each element assigned to a well
	TVD_elem : array
	  Contains the masl data at the middle for each element assigned to a well
	TVD_elem_top : array
	  Contains the masl data at the top  for each element assigned to a well
	layer_bottom : array
	  Contains the masl data at the bottom for each element assigned to a well

	Note
	----
	The real data is taken from the the sqlite database

	"""

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	PT_real_dictionary={}

	try:

		#Plotting real data
		data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%well,conn)

		x_T,y_T,z_T,var_T=geomtr.MD_to_TVD_one_var_array(well,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

		x_P,y_P,z_P,var_P=geomtr.MD_to_TVD_one_var_array(well,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)

		PT_real_dictionary['x_T']=x_T
		PT_real_dictionary['y_T']=y_T
		PT_real_dictionary['z_T']=z_T
		PT_real_dictionary['var_T']=var_T

		PT_real_dictionary['x_P']=x_P
		PT_real_dictionary['y_P']=y_P
		PT_real_dictionary['z_P']=z_P
		PT_real_dictionary['var_P']=var_P

		no_real_data=False

	except ValueError:

		data_PT_real=None

		no_real_data=True

		print("No real data for %s"%well)

	#Preparing the input file from the t2 results

	in_file="%s/%s_PT.dat"%(inpath,well)

	if os.path.isfile(in_file):

		data=pd.read_csv(in_file)

		data[['correlative']]=data.ELEM.apply(lambda x: pd.Series(str(x)[0]))

		data.sort_values(by='correlative' , inplace=True)

		#Retrieving the layers information from model_conf

		layers_info=geomtr.vertical_layers(input_dictionary)

		TVD_elem=layers_info['middle']

		TVD_elem_top=layers_info['top']

		layer_bottom={layers_info['name'][n]:layers_info['bottom'][n] for n in range(len(layers_info['name']))}

		conn.close()

		return data_PT_real, no_real_data, data, TVD_elem, TVD_elem_top, PT_real_dictionary, layer_bottom

	else:
		sys.exit("The file %s or directory do not exist"%in_file)

def image_save_all_plots(typePT,input_dictionary,width=4,height=4.5):
	"""It plots all the wells defined on input_dictionay and compare real data with model output
	
	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path', list of wells under the keywords 'WELLS', 'MAKE_UP_WELLS' and 'NOT_PRODUCING_WELL'. Lastly, it contains the information of the top level of the mesh on under the key 'z_ref'
	typePT : str
	  'T' for temperature or 'P' for pressure
	height : float
	  Defines the ratio height/width
	width  : float
	  By dividing the number of wells defines the number of rows on the chart


	Returns
	-------
	image
		{typePT}_all.png: on path ../output/PT/images/logging/

	Note
	----
	The real data is taken from the the sqlite database. Depending on the number of wells defined the default values for width and height migth be changed

	Examples
	--------
	>>> image_save_all_plots(typePT='T',input_dictionary)
	"""

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	db_path=input_dictionary['db_path']

	limit_layer='M'

	fontsizex=4

	fontsize_layer=3

	rows=int(math.ceil(len(wells)/width))

	widths=[1 for n in range(width)]

	#heights=[int(2*(40.0/3)*len(widths)/int(math.ceil(len(wells)/3.0)))+1 for n in range(int(math.ceil(len(wells)/3.0)))]

	heights=[height for n in range(rows)]

	#gs = gridspec.GridSpec(nrows=len(heights), ncols=len(widths), width_ratios=widths, height_ratios=heights,hspace=0.8, wspace=0.7)

	gs = gridspec.GridSpec(nrows=rows, ncols=4,width_ratios=widths, height_ratios=heights,hspace=0.5, wspace=0.25)

	fig= plt.figure(figsize=(8.5,rows*3), dpi=100)

	fig.suptitle("%s Calculated vs  %s Measured"%(typePT,typePT), fontsize=10)

	conn=sqlite3.connect(db_path)

	c=conn.cursor()

	layers_info=geomtr.vertical_layers()

	layer_bottom={layers_info['name'][n]:layers_info['bottom'][n] for n in range(len(layers_info['name']))}

	TVD_elem=layers_info['middle']

	TVD_elem_top=layers_info['top']

	ymin=float(pd.read_sql_query("SELECT bottom FROM layers WHERE correlative='%s';"%limit_layer,conn)['bottom'])

	if typePT in ['P','T']:
		if typePT=='P':
			data_to_extract='Pressure'
			label_name='Pressure [bar]'
			data_lims=[0,150]
			divisor=1E5
		elif typePT=='T':
			data_to_extract='Temperature'
			data_lims=[50,260]
			divisor=1
			label_name='Temperature [$^\circ$C]'

		for i, name in enumerate(wells):

			#Real data
			data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

			if len(data_PT_real)>0:

				x_T,y_T,z_T,var_T=geomtr.MD_to_TVD_one_var_array(name,data_PT_real[data_to_extract].values,data_PT_real['MeasuredDepth'].values,100)

				#Define plot

				axT= fig.add_subplot(gs[i])
				
				ln1T=axT.plot(var_T,z_T,color=plot_conf_color[typePT][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=0.5,label='Measured')

				#Model

				in_file="../output/PT/txt/%s_PT.dat"%name

				if os.path.isfile(in_file):

					data=pd.read_csv(in_file)

					blk_num=data['ELEM'].values

					data[['correlative']]=data.ELEM.apply(lambda x: pd.Series(str(x)[0]))

					data.sort_values(by='correlative' , inplace=True)

					ln2T=axT.plot(np.array(data[typePT])/divisor,np.array(TVD_elem),linestyle='None',color=plot_conf_color[typePT][0],marker=plot_conf_marker['current'][0],ms=1,label='Calculated')

					axT.set_ylim([layer_bottom[limit_layer],z_ref])
					
					axT.set_xlim(data_lims)

					ax2T = axT.twinx()

					ax2T.set_yticks(TVD_elem_top,minor=True)

					ax2T.set_yticks(TVD_elem,minor=False)
					
					ax2T.tick_params(axis='y',which='major',length=0)

					ax2T.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

					ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

					ax2T.set_ylim(axT.get_ylim())

					lnsT = ln1T+ln2T

					labsT = [l.get_label() for l in lnsT]

					axT.legend(lnsT, labsT, loc='lower left', fontsize=fontsizex)

					axT.set_xlabel('%s\n %s'%(name,label_name),fontsize=fontsizex+2)

					axT.xaxis.set_label_coords(0.5,1.3)

					axT.yaxis.set_label_coords(-0.07,0.5)

					axT.xaxis.tick_top()

					axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

					axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

					plt.draw()

		plt.subplots_adjust(top=0.9)

		fig.savefig("../report/images/PT/%s_all.png"%typePT) 
	else:
		sys.exit("There is no real data for the parameter selected: %s "%typePT)

