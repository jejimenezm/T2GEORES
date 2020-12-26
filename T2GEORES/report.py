import sys
from model_conf import *
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
from model_conf import input_data,geners,mesh_setup
import t2_writer as t2w
from formats import formats_t2
import geometry as geomtr
from formats import plot_conf_color,plot_conf_marker

#It is a must to change the way a json is loaded

def plot_compare_one(well,savefig,data_PT_real, no_real_data, data, TVD_elem, TVD_elem_top,axT,axP,PT_real_dictionary,layer_bottom,limit_layer,input_dictionary,label=None,def_colors=True):
	"""Genera una area con dos graficas, en una se muestra la grafica de temperatura real y la temperatura calculada vs la profundidad real, en la otra la presion real y la calculada vs la profundidad real.

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	well : str
	  Nombre de pozo
	inpath : str
	  Direccion de archivo de entrada
	savefig : bool
	  Al ser cierto guarda la grafica generada

	Returns
	-------
	image
		PT_{well}.png: archivo con direccion ../output/PT/images/logging


	Note
	----
	La temperatura rel es tomada de la base de datos

	Examples
	--------
	>>> plot_compare_one(db_path,='AH-34',"../output/PT/txt",savefig=True)
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

def plot_compare_one_data(well,input_dictionary=input_data,inpath="../output/PT/txt"):
	"""Genera una area con dos graficas, en una se muestra la grafica de temperatura real y la temperatura calculada vs la profundidad real, en la otra la presion real y la calculada vs la profundidad real.

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	well : str
	  Nombre de pozo
	inpath : str
	  Direccion de archivo de entrada
	savefig : bool
	  Al ser cierto guarda la grafica generada

	Returns
	-------
	image
		PT_{well}.png: archivo con direccion ../output/PT/images/logging


	Note
	----
	La temperatura rel es tomada de la base de datos

	Examples
	--------
	>>> plot_compare_one(db_path,='AH-34',"../output/PT/txt",savefig=True)
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



def image_save_all_plots(typePT,db_path=input_data['db_path'],wells=[i for x in ['WELLS','NOT_PRODUCING_WELL'] for i in input_data[x]],z_ref=input_data['z_ref']):
	"""Genera una grafica con multiples areas donde se compara la temperatura o presion real y la calculada vs la profundidad vertical

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Nombres de de pozos
	typePT : str
	  'T' o 'P', segun se necesite
	savefig : bool
	  Al ser cierto guarda la grafica generada

	Other Parameters
	----------------
	array
		widths : arreglo con relacion altura/ancho de cada grafico

	Returns
	-------
	image
		{typePT}_all.png: archivo con direccion ../output/PT/images/logging/

	Note
	----
	La temperatura real es tomada de la base de datos. Probablemente los argumentos hspace y wspace deban ser modificados, asicomo el tamanio de la figura

	Examples
	--------
	>>> image_save_all_plots(db_path,wells,'T')
	"""

	limit_layer='M'

	fontsizex=4

	fontsize_layer=3

	rows=int(math.ceil(len(wells)/4.0))

	widths=[1 for n in range(4)]

	#heights=[int(2*(40.0/3)*len(widths)/int(math.ceil(len(wells)/3.0)))+1 for n in range(int(math.ceil(len(wells)/3.0)))]

	heights=[4.5 for n in range(rows)]

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

#Not the best results
def plot_layer_from_json(layer,method,ngridx,ngridy,save,show,print_points,print_eleme_name,variable_to_plot,source,print_mesh,print_well,use_lim,variable_local_limit=False):
	"""Genera un corte en la capa especificada de la variable y fuente especificada

	Parameters
	----------	  
	layer : str
	  Nombre de capa
	method : str
	  Tipo de metodo para interpolacion
	ngridx : int
	  Numero de elementos en grid regular en direccion horizontal
	ngridy : int
	  Numero de elementos en grid regular en direccion vertical
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada
	print_points : bool
	  Imprime los centros de cada elemento
	print_eleme_name : bool
	  Imprime los nombres de los elementos
	variable_to_plot : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW" para fuente t2 y "P" y "T" para sav
	source : str
	  Fuente de informacion, json generado a partir de "sav" o "t2"
	print_mesh : bool
	  Imprime la malla
	print_well : bool
	  Imprime el nombre del pozo

	Other Parameters
	----------------
	float
		extent_X_min : limite horizontal menor de zoom
	float
		extent_X_max : limite horizontal mayor de zoom
	float
		extent_Y_min : limite vertical menor de zoom
	float
		extent_y_max : limite vertical mayor de zoom
	bool
		use_lim : Utiliza limites definodos
	int
		fontsize_labels: tamanio de letra en contornos

	Returns
	-------
	image
		layer_{capa}_{variable}.png: archivo con direccion ../output/PT/images/layer/layer_%s_%s.png

	Note
	----
	Probablemente sea necesario modificar el tamani de las fuentes

	Examples
	--------
	>>> plot_layer_from_json('D','linear',1000,1000,save=True,show=True,print_points=False,print_eleme_name=False,variable_to_plot="P",source="t2",print_mesh=False,print_well=True)
	"""
	fontsize_labels=6

	if source=="sav":
		file="../output/PT/json/PT_json_from_sav.txt"
		variables=["P","T"]
	elif source=="t2":
		file="../output/PT/json/PT_json.txt"
		variables=["P","T","SG","SW","X1","X2","PCAP","DG","DW"]

	with open("../mesh/well_dict.txt","r") as well_f:
			well_correlatives=json.load(well_f)

	if os.path.isfile(file):
		if variable_to_plot in variables:
			with open(file,"r") as f:
				data=json.load(f)
			element_name=[]
			x=[]
			y=[]
			z=[]
			variable=[]

			variable_min=100E8
			variable_max=0

			for elementx in data:
				if layer==elementx[0]:
					x.append(data[elementx]['X'])
					y.append(data[elementx]['Y'])
					z.append(data[elementx]['Z'])
					variable.append(data[elementx][variable_to_plot])
					element_name.append(elementx)
					if variable_local_limit:
						if variable_max<data[elementx][variable_to_plot]:
							variable_max=data[elementx][variable_to_plot]

						if variable_min>data[elementx][variable_to_plot]:
							variable_min=data[elementx][variable_to_plot]

				if not variable_local_limit:
					if variable_max<data[elementx][variable_to_plot]:
						variable_max=data[elementx][variable_to_plot]

					if variable_min>data[elementx][variable_to_plot]:
						variable_min=data[elementx][variable_to_plot]


			variable_levels=np.linspace(variable_min,variable_max,num=10)

			xi = np.linspace(min(x), max(x), ngridx)
			yi = np.linspace(min(y), max(y), ngridy)

			zi = griddata((x, y), variable, (xi[None,:], yi[:,None]), method=method)

			fig=plt.figure(figsize=(10,8))

			ax1=fig.add_subplot(1,1,1)

			if variable_levels[0]!=variable_levels[-1]:
				contourax1=ax1.contour(xi,yi,zi,15,linewidths=0.5,colors='k',levels=variable_levels)
				cntr3 = ax1.contourf(xi,yi,zi,15,cmap="jet",levels=variable_levels)
				ax1.clabel(contourax1, inline=1, fontsize=fontsize_labels,fmt='%10.0f',colors='black')
			else:
				contourax1=ax1.contour(xi,yi,zi,15,linewidths=0.5,colors='k')
				cntr3 = ax1.contourf(xi,yi,zi,15,cmap="jet")
				ax1.clabel(contourax1, inline=1, fontsize=fontsize_labels,fmt='%10.0f',colors='black')

			fig.colorbar(cntr3,ax=ax1)

			if print_points:
				ax1.plot(x,y,'ok',ms=1)

			if print_eleme_name:
				for n in range(len(element_name)):
					ax1.text(x[n],y[n], element_name[n], color='k',fontsize=4)

			if print_well:
				for n in range(len(element_name)):
					if element_name[n] in well_correlatives.keys():
						ax1.text(x[n],y[n],well_correlatives[element_name[n]][0], color='k',fontsize=5)

			if print_mesh:
				mesh_segment=open("../mesh/to_steinar/segmt","r")
				lines_x=[]
				lines_y=[]
				for line in mesh_segment:
					lines_x.append([float(line[0:15]),float(line[30:45])])
					lines_y.append([float(line[15:30]),float(line[45:60])])

				ax1.plot(np.array(lines_x).T,np.array(lines_y).T,'-k',linewidth=0.1,alpha=0.75)

			ax1.tick_params(axis='both', which='major', labelsize=6,pad=1)
			ax1.set_ylabel('North [m]',fontsize = 8)
			ax1.set_xlabel('East [m]',fontsize=8)
			ax1.set_title("Layer %s"%layer,fontsize=10)
			
			if use_lim:	
				ax1.set_xlim([mesh_setup['Xmax'],mesh_setup['Xmin']])
				ax1.set_ylim([mesh_setup['Ymin'],mesh_setup['Ymax']])
			if save:
				fig.savefig("../output/PT/images/layer/layer_%s_%s.png"%(layer,variable_to_plot)) 
			if show:
				plt.show()
		else:
			print("The variable to plot does not exist on this file %s"%variable_to_plot)
	else:
		print("The PT_json file does not exist, run extract_json_from_t2out  or from_sav_to_json from output.py first")

def plot_all_layer(variable_to_plot='SG',source="t2"):
	"""Configura la funcion plot_layer_from_json de forma que almacenen las imagenes de todos las capas para un parametros en particular

	Returns
	-------
	image
		layer_{capa}_{variable}.png: archivo con direccion ../output/PT/images/layer/layer_%s_%s.png para todas las capas de un parametro en especifico.

	Note
	----
	Debera modificarse la funcion plot_layer_from_json de forma interna de forma que se ajuste a la salida desea

	Examples
	--------
	>>> plot_all_layer()
	"""
	layers_info=geomtr.vertical_layers()

	for layer in layers_info['name']:
		plot_layer_from_json(layer,'linear',1000,1000,save=True,show=False,print_points=True,print_eleme_name=False,\
			variable_to_plot=variable_to_plot,source=source,print_mesh=False,print_well=True,use_lim=True)

def plot_compare_PT_curr_prev(well,show,db_path=input_data['db_path'],inpath="../output/PT/txt",previnpath="../output/PT/txt/prev"):
	"""Genera una area con dos graficas, en una se muestra la grafica de temperatura real, calculada actual y previa vs la profundidad real, en la otra la presion real, calculada actual y previa vs la profundidad real.

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	well : str
	  Nombres de pozo
	show : bool
	  Al ser cierto muestra
	inpath : str
	  Direccion de archivo de entrada
	previnpath : str
	  Direccion de archivo de entrada

	Returns
	-------
	image
		PT_{pozo}.png: archivo con direccion '../calib/PT/images/PT_%s.png'

	Note
	----
	Debe existir registro en la carpeta prev del folder ../output/PT

	Examples
	--------
	>>> plot_compare_PT_curr_prev(db_path,well,"../output/PT/txt","../output/PT/txt/prev",show=False)
	"""


	fontsize_plot=6

	fontsize_layer=6

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Define plot
	fig= plt.figure(figsize=(10, 10), dpi=100)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	#Real data
	data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%well,conn)

	#Plotting real data
	try:
		x_T,y_T,z_T,var_T=geomtr.MD_to_TVD_one_var_array(well,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)
		ln1T=axT.plot(var_T,z_T,color=plot_conf_color['T'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')
	except ValueError:
		print("No measured temperature was found for %s or it is not  yet on the database"%well)
		ln1T=axT.plot([],[],label='Measured')
	lnsT=ln1T

	try:
		x_P,y_P,z_P,var_P=geomtr.MD_to_TVD_one_var_array(well,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)
		ln1P=axP.plot(var_P,z_P,color=plot_conf_color['P'][0],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')
	except ValueError:
		print("No measured pressure was found for %s or it is not  yet on the database"%well)
		ln1P=axP.plot([],[],label='Measured')
	lnsP=ln1P

	#Model

	in_file="%s/%s_PT.dat"%(inpath,well)

	prev_in_file="%s/%s_PT.dat"%(previnpath,well)

	if os.path.isfile(in_file):

		data=pd.read_csv(in_file)

		if len(data)>0:

			data[['correlative']]=data.ELEM.apply(lambda x: pd.Series(str(x)[0]))

			data.sort_values(by='correlative' , inplace=True)

			#Retrieving the layers information from model_conf

			layers_info=geomtr.vertical_layers()

			TVD_elem=layers_info['middle']

			TVD_elem_top=layers_info['top']

			#Plotting the calculated data

			ln2T=axT.plot(data['T'],TVD_elem,linestyle='None',color=plot_conf_color['T'][0],marker=plot_conf_marker['current'][0],label='Current')

			ln2P=axP.plot(data['P']/1E5,TVD_elem,linestyle='None',color=plot_conf_color['P'][0],marker=plot_conf_marker['current'][0],label='Current')

			ax2P = axP.twinx()

			ax2P.set_yticks(TVD_elem_top,minor=True)

			ax2P.set_yticks(TVD_elem,minor=False)

			ax2P.tick_params(axis='y',which='major',length=0)

			ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.5, lw=0.5)

			ax2P.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

			ax2P.set_ylim(axP.get_ylim())

			ax2T = axT.twinx()

			ax2T.set_yticks(TVD_elem_top,minor=True)

			ax2T.set_yticks(TVD_elem,minor=False)
			
			ax2T.tick_params(axis='y',which='major',length=0)

			ax2T.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

			ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.5, lw=0.5)

			ax2T.set_ylim(axT.get_ylim())

			lnsT+=ln2T
			lnsP+=ln2P
		else:
			print("No output data on current model for well %s"%well)

	if os.path.isfile(prev_in_file):

		data=pd.read_csv(prev_in_file)

		if len(data)>0:

			data[['correlative']]=data.ELEM.apply(lambda x: pd.Series(str(x)[0]))

			data.sort_values(by='correlative' , inplace=True)

			layers_info=geomtr.vertical_layers()

			TVD_elem=layers_info['middle']

			TVD_elem_top=layers_info['top']

			ln3T=axT.plot(data['T'],TVD_elem,linestyle='None',color=plot_conf_color['T'][0],marker=plot_conf_marker['previous'][0],linewidth=1,label='Previous calculated')

			ln3P=axP.plot(data['P']/1E5,TVD_elem,linestyle='None',color=plot_conf_color['P'][0],marker=plot_conf_marker['previous'][0],linewidth=1,label='Previous calculated')

			lnsT +=ln3T
			lnsP +=ln3P
		else:
			print("No output data on the previous model for well %s"%well)

	labsT = [l.get_label() for l in lnsT]

	axT.legend(lnsT, labsT, loc='lower left', fontsize=fontsize_plot)

	axT.set_xlabel('Temperature [$^\circ$C]',fontsize=fontsize_plot)

	axT.xaxis.set_label_coords(0.5,1.05)

	axT.xaxis.tick_top()

	axT.set_ylabel('m.a.s.l.',fontsize = fontsize_plot)

	axT.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	labsP = [l.get_label() for l in lnsP]

	axP.legend(lnsP, labsP, loc='lower left', fontsize=fontsize_plot)
	
	axP.set_xlabel('Pressure [bar]',fontsize=fontsize_plot)

	axP.xaxis.set_label_coords(0.5,1.05)

	axP.xaxis.tick_top()

	axP.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	plt.subplots_adjust(top=0.92)

	fig.suptitle("%s"%well, fontsize=fontsize_plot)
	
	if  os.path.isfile(prev_in_file) and  os.path.isfile(in_file):
		fig.savefig('../calib/PT/images/PT_%s.png'%well) 

	if show:
		plt.show()

	return fig

def compare_runs_PT(wells=[i for x in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL'] for i in input_data[x]],title=input_data['TITLE']):
	"""Genera un archivo pdf donde se compara la temperatura y presion real vs la calculada actual y previa

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Nombres de pozo
	title : str
	  Nombre del modelo tomado del model_conf

	Returns
	-------
	pdf
		run_{date-time}.pdf: archivo con direccion ../calib/PT/

	Note
	----
	Debe existir registro en la carpeta prev del folder ../output/PT

	Examples
	--------
	>>> compare_runs_PT(wells,db_path)
	"""

	pdf_pages=PdfPages('../calib/PT/run_'+str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))+'.pdf')
	for well in sorted(wells):
		fig=plot_compare_PT_curr_prev(well=well,show=False)
		pdf_pages.savefig(fig)

	d = pdf_pages.infodict()
	d['Title'] = title
	d['Author'] = 'Author'
	d['Subject'] = 'Field'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()

	# Write the PDF document to the disk
	pdf_pages.close()


def vertical_cross_section(method,ngridx,ngridy,variable_to_plot,source,show_wells_3D,print_point,savefig,plots_conf,input_dictionary=input_data):
	"""Genera un corte vertical en la trayectoria de una linea de una propiedad especificada

	Parameters
	----------	  
	method : str
	  Tipo de metodo para interpolacion
	ngridx : int
	  Numero de elementos en grid regular en direccion del corte
	ngridy : int
	  Numero de elementos en grid regular en direccion vertical
	show_wells_3D : bool
	  Muestra la geometria del pozo en 3D
	print_point : bool
	  Imprime los puntos donde se ha extraido informacion ya sea interpolada o no
	variable_to_plot : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW" para fuente t2 y "P" y "T" para sav
	savefig : bool
	  Al ser cierto guarda la grafica generada

	Other Parameters
	----------------
	array
		x_points : coordenada x de linea
	array
		y_points : coordenada y de linea

	Returns
	-------
	image
		vertical_section_{varible_to_plot}.png: archivo con direccion '../output/PT/images/

	Note
	----
	La proyeccion de los pozos funciona correctamente cuando el pozo no se encuentre entre los vertices de la linea definida para el corte

	Examples
	--------
	>>> vertical_cross_section(method='cubic',ngridx=100,ngridy=100,variable_to_plot="T",source="t2",show_wells_3D=True)
	"""
	x_points=plots_conf['cross_section']['x']
	y_points=plots_conf['cross_section']['y']
	variable_levels=plots_conf['variable_levels']

	variables_to_plot_t2={"P":4,
						   "T":5,
						   "SG":6,
						   "SW":7,
						   "X1":8,
						   "X2":9,
						   "PCAP":10,
						   "DG":11,
						   "DW":12}

	variables_to_plot_sav={"P":3,
	                       "T":4}

	if source=="sav":
		index=variables_to_plot_sav[variable_to_plot]
		file="../output/PT/json/PT_json_from_sav.txt"
	elif source=="t2":
		index=variables_to_plot_t2[variable_to_plot]
		file="../output/PT/json/PT_json.txt"

	if os.path.isfile(file):
		with open(file,"r") as f:
	  		data=json.load(f)
	  	

	variable_min=100E8
	variable_max=0

	#Creates an irregular grid with the form [[x,y,z],[x1,y1,z1]]
	irregular_grid=np.array([[0,0,0]])
	variable=np.array([])
	for elementx in data:
		if variable_max<data[elementx][variable_to_plot]:
			variable_max=data[elementx][variable_to_plot]

		if variable_min>data[elementx][variable_to_plot]:
			variable_min=data[elementx][variable_to_plot]

		irregular_grid=np.append(irregular_grid,[[data[elementx]['X'],data[elementx]['Y'],data[elementx]['Z']]],axis=0)
		variable=np.append(variable,data[elementx][variable_to_plot])


	irregular_grid=irregular_grid[1:]
	variable=variable[0:]


	#Creates the points a long the lines
	x=np.array([])
	y=np.array([])
	
	for xy in range(len(x_points)):
		if xy < len(x_points)-1:
			xt=np.linspace(x_points[xy],x_points[xy+1]+(x_points[xy+1]-x_points[xy])/ngridx,num=ngridx)
			yt=np.linspace(y_points[xy],y_points[xy+1]+(y_points[xy+1]-y_points[xy])/ngridy,num=ngridy)
			x=np.append(x,xt)
			y=np.append(y,yt)

	#Calculastes the distance of every point along the projection

	projection_req=np.array([0])
	for npr in range(1,len(x)):
		if npr==len(x)-1:
			break
		if npr==1:
			delta_x_pr=(x_points[0]-x[0])**2
			delta_y_pr=(y_points[0]-y[0])**2
			prj_prox=(delta_y_pr+delta_x_pr)**0.5
		else:
			delta_x_pr=(x[npr+1]-x[npr])**2
			delta_y_pr=(y[npr+1]-y[npr])**2
			prj_prox=(delta_y_pr+delta_x_pr)**0.5
		projection_req=np.append(projection_req,prj_prox+projection_req[npr-1])

	layers_info=geomtr.vertical_layers(input_dictionary)

	zmid=layers_info['middle']

	ztop=layers_info['top']

	zbottom=layers_info['bottom']

	zlabels=layers_info['name']

	#Creates the regular  mesh in 3D along all the layers

	xi = np.linspace(min(x), max(x), ngridx)
	yi = np.linspace(min(y), max(y), ngridy)
	zi = np.array(zmid)

	proj_req=np.array([])
	z_req_proj=np.array([])

	for nprj in range(len(projection_req)):
		for nz in range(len(zi)):
			proj_req=np.append(proj_req,projection_req[nprj])
			z_req_proj=np.append(z_req_proj,zi[nz])

	request_points=np.array([[0,0,0]])
	x_req=np.array([])
	y_req=np.array([])
	z_req=np.array([])


	for nx in range(len(x)):
		for nz in range(len(zi)):
			request_points= np.append(request_points,[[x[nx],y[nx],zi[nz]]],axis=0)
			x_req=np.append(x_req,x[nx])
			y_req=np.append(y_req,y[nx])
			z_req=np.append(z_req,zi[nz])

	request_points=request_points[1:]

	requested_values = griddata(irregular_grid, variable, request_points)

	#Creates regular mesh on projection

	xi_pr = np.linspace(min(proj_req), max(proj_req), 1000)
	yi_pr = np.linspace(min(z_req_proj), max(z_req_proj), 1000)
	zi_pr = griddata((proj_req, z_req_proj), requested_values[:-len(zmid)], (xi_pr[None,:], yi_pr[:,None]))

	fig = plt.figure()

	#Plot projection
	
	ax = fig.add_subplot(211)


	ax.text(0,1.05, "A",color='black',transform=ax.transAxes)
	ax.text(1,1.05, "A'",color='black',transform=ax.transAxes)
	ax.set_xlabel('distance [m]')
	ax.set_ylabel('masl')

	contourax=ax.contour(xi_pr,yi_pr,zi_pr,15,linewidths=0.5,colors='k',levels=variable_levels)
	cntr = ax.contourf(xi_pr,yi_pr,zi_pr,15,cmap="jet",levels=variable_levels)
	
	if print_point:
		ax.plot(proj_req,z_req_proj,'ok',ms=0.5)
	
	ax.clabel(contourax, inline=1, fontsize=6,fmt='%10.0f',colors="k")

	cbar=fig.colorbar(cntr,ax=ax)
	cbar.set_label('Temperature [$^\circ$C]') #Fix it
	#Scatter 3D

	ax3D = fig.add_subplot(212, projection='3d')

	colorbar_source=ax3D.scatter3D(x_req,y_req,z_req,cmap='jet',c=requested_values)

	ax3D.set_xlabel('East [m]')
	ax3D.set_ylabel('North [m]')
	ax3D.set_zlabel('m.a.s.l.')
	fig.colorbar(colorbar_source, ax=ax3D)
	

	#Projects well on slice
	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	for name in sorted(input_dictionary['WELLS']):
		data_position=pd.read_sql_query("SELECT east,north,elevation FROM wells WHERE well='%s';"%name,conn)
		data=pd.read_sql_query("SELECT MeasuredDepth FROM survey WHERE well='%s' ORDER BY MeasuredDepth;"%name,conn)

		x_real=[]
		y_real=[]
		z_real=[]
		well_proj=[]

		for v in range(len(data['MeasuredDepth'])):
			xf,yf,zf=geomtr.MD_to_TVD(name,data['MeasuredDepth'][v])
			x_real.append(float(xf))
			y_real.append(float(yf))
			z_real.append(float(zf))
		
		for ny in range(len(y_points)):
			if data_position['north'][0]>y_points[ny]:
				position=ny
				bx=x_points[position+1]-x_points[position]
				by=y_points[position+1]-y_points[position]
				br=(bx**2+by**2)**0.5
		
	
		for n_proj in range(len(x_real)):
			delta_x=x_real[n_proj]-x_points[position]
			delta_y=y_real[n_proj]-y_points[position]
			r=(delta_y**2+delta_x**2)**0.5
			proj_w=((bx*delta_x)+(by*delta_y))/br
			print(n_proj)
			well_proj.append(proj_w)
			if n_proj==0:
				d=(r**2-proj_w**2)**0.5
		if d<200:
			ax.annotate(name,
            xy=(well_proj[0], z_real[0]), 
            xytext=(well_proj[0]+200, z_real[0]), 
            arrowprops=dict(arrowstyle="->",
                            connectionstyle="arc3"),
            )
			ax.plot(well_proj,z_real,'-k',ms=0.5)
		
	conn.close()


	#Plot wells on 3D

	if show_wells_3D:
		conn=sqlite3.connect(input_dictionary['db_path'])
		c=conn.cursor()

		for name in sorted(input_dictionary['WELLS']):
			data_position=pd.read_sql_query("SELECT east,north,elevation FROM wells WHERE well='%s';"%name,conn)
			data=pd.read_sql_query("SELECT MeasuredDepth FROM survey WHERE well='%s' ORDER BY MeasuredDepth;"%name,conn)
			
			ax3D.text(data_position['east'][0], data_position['north'][0], data_position['elevation'][0], \
				      name, color='black',alpha=0.75,fontsize=8)

			x_real=[]
			y_real=[]
			z_real=[]

			for v in range(len(data['MeasuredDepth'])):
				xf,yf,zf=geomtr.MD_to_TVD(name,data['MeasuredDepth'][v])
				x_real.append(float(xf))
				y_real.append(float(yf))
				z_real.append(float(zf))
		
			ax3D.plot3D(x_real, y_real, z_real,'-k',alpha=0.75)

		conn.close()
	if savefig:
		fig.savefig('../output/PT/images/vertical_section_%s.png'%variable_to_plot) 

	plt.show()

def plot_evol_well_data(well,layer,parameter,input_dictionary=input_data):
	"""Genera una linea de evolucion de un parametro en particular a lo largo del tiempo a partir de un tiempo de referencia y los compara con su valor real

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	layer : str
	  Nombre de capa de parametro selecionado
	ngridy : int
	  Numero de elementos en grid regular en direccion vertical
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Muestra la grafica
	parameter : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"

	Returns
	-------
	image
		{pozo}_{capa}_{parametro}_evol.png: archivo con direccion '../output/PT/images/evol/%s_%s_%s_evol.png'

	Note
	----
	Toma los datos de los archivo de entrada en ../input/drawdown e ../input/cooling, cualquier otro parametro solo ser graficado, sin comparacion alguna.

	Examples
	--------
	>>> vplot_PT_evol_block_in_wells('CHI-6A',layer='E',parameter='T',save=True,show=True)
	"""
	if parameter  not in ["P","T","SG","SW","X(WAT1)","X(WAT2)","PCAP","DG","DW"]:
		print("Cant be printed, the parameter is  not register")
	elif parameter=="P":
		parameter_label="Pressure"
		parameter_unit="bar"
		file="../input/drawdown/%s_DD.dat"%well
		header='pressure'
	elif parameter=="T":
		parameter_label="Temperature"
		parameter_unit="C"
		file="../input/cooling/%s_C.dat"%well
		header='temperature'

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

	color_real=plot_conf_color[parameter][0]
	color_calc=plot_conf_color[parameter][1]
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
				dates.append(input_dictionary['ref_date']+datetime.timedelta(days=int(times[n])))
				if parameter!="P":
					values_to_plot.append(values[n])
				else:
					values_to_plot.append(values[n]/1E5)
					
			except OverflowError:
				print(input_dictionary['ref_date'],"plus",str(times[n]),"wont be plot")

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	depth=pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%layer,conn)

	depth=depth.values[0][0]


	#Read file, real
	
	try:
		check_res=False
		if parameter=="P":
			if well!='AH-25' or layer!='E':
				file="../input/drawdown/%s_DD.dat"%well
			elif well=='AH-25' and layer=='E':
				file="../input/drawdown/p_res.csv"
				check_res=True
		elif parameter=="T":	
			file="../input/cooling/%s_C.dat"%well

		data_real=pd.read_csv(file)
		
	except IOError:
		data_real=None
		print("No real data exist")
		pass


	calculated={'dates':dates,'values':values_to_plot}

	"""
	fig, ax = plt.subplots(figsize=(10,4))
	ax.plot(dates,values_to_plot,'-o',color=color_real,linewidth=1,ms=3,label='Calculated %s'%parameter_label)
	try:
		if not check_res:
			ax.plot(dates_real,data_real.loc[data_real['TVD']==depth][header].values,'-o',color=color_calc,linewidth=1,ms=3,label='Real %s'%parameter_label)
		if check_res:
			ax.plot(dates_real,data_real['Pres'].values,'-o',color=color_calc,linewidth=1,ms=3,label='Real %s'%parameter_label)
	except UnboundLocalError:
		pass
	ax.set_title("Well: %s at %s masl (layer %s)"%(well,depth,layer) ,fontsize=8)
	ax.set_xlabel("Time",fontsize = 8)
	ax.set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)

	ax.legend(loc="upper right")

	#Plotting formating
	#xlims=[min(dates)-datetime.timedelta(days=365),max(dates)+datetime.timedelta(days=365)]
	xlims=[ref_date-datetime.timedelta(days=365),ref_date+datetime.timedelta(days=60*365.25)]
	
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	ax.set_xlim(xlims)
	
	#Use Y lims
	#ylims=[val_min,val_max]
	#ax.set_ylim(ylims)

	ax.xaxis.set_major_formatter(years_fmt)

	#ax.xaxis.set_major_locator(years)
	#fig.autofmt_xdate()

	#Grid style
	ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.grid(True)

	if save:
		fig.savefig('../output/PT/images/evol/%s_%s_%s_evol.png'%(well,layer,parameter)) 
	if show:
		plt.show()
	"""
	return calculated,data_real,depth,header,parameter_label,parameter_unit

def plot_evol_well_lines(calculated,real_data,parameter,depth,header,well,layer,parameter_unit,parameter_label,label,ax,input_dictionary=input_data,years=15,color_def=False):

	dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
	
	line,=ax.plot(calculated['dates'],calculated['values'],'-o',linewidth=1,ms=2,label='Calculated %s'%label)
	if color_def:
		color=plot_conf_color[parameter][1]
		line.set_color(color)

	if real_data!=None:
		dates_real=list(map(dates_func,real_data.loc[real_data['TVD']==depth]['datetime'].values))
		ax.plot(dates_real,real_data.loc[real_data['TVD']==depth][header].values,marker=plot_conf_marker['real'][0],linestyle='None',color=plot_conf_color[parameter][0],linewidth=1,ms=3,label='Real %s'%well)

	ax.set_title("Well: %s at %s masl (layer %s)"%(well,depth,layer) ,fontsize=8)
	ax.set_xlabel("Time",fontsize = 8)
	ax.set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)

	ax.legend(loc="upper right")

	xlims=[input_dictionary['ref_date'],input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]
	
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	ax.set_xlim(xlims)
	
	ax.xaxis.set_major_formatter(years_fmt)

	#Grid style
	ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.grid(True)


def plot_evol_well(well,layer,parameter,save,show):

	fig, ax = plt.subplots(figsize=(10,4))

	calculated,real_data,depth,header,parameter_label,parameter_unit=plot_evol_well_data(well,layer,parameter)

	plot_evol_well_lines(calculated,real_data,parameter,depth,header,well,layer,parameter_unit,parameter_label,ax=ax)

	if save:
		fig.savefig('../output/PT/images/evol/%s_%s_%s_evol.png'%(well,layer,parameter)) 
	if show:
		plt.show()

"""
wells=['AH-34A','AH-1']
fig, ax = plt.subplots(figsize=(10,4))
for well in wells:
	calculated,real_data,depth,header,parameter_label,parameter_unit=plot_evol_well_data(well,'E','P')
	plot_evol_well_lines(calculated,real_data,'P',depth,header,well,'E',parameter_unit,parameter_label,well,ax=ax)
plt.show()
"""

#plot_PT_evol_block_in_wells(well,layer,parameter,save,show)


def save_all_PT_evol_from_layer(wells,layer,parameter):
	"""Genera y almacena todas las graficas de un parametro defino en una capa especifica

	Parameters
	----------	  
	wells : array
	  Nombres de pozo
	layer : str
	  Nombre de capa de parametro selecionado
	parameter : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"

	Returns
	-------
	image
		{pozo}_{capa}_{parametro}_evol.png: archivo con direccion ../output/PT/images/evol

	Note
	----
	Toma los datos de los archivo de entrada en ../input/drawdown e ../input/cooling, cualquier otro parametro solo ser graficado, sin comparacion alguna.

	Examples
	--------
	>>> plot_PT_evol_block_in_wells('CHI-6A',layer='E',parameter='T',save=True,show=True)
	"""
	save=True
	for well in wells:
		plot_PT_evol_block_in_wells(well,layer,parameter,save,show=False)

def plot_compare_evol_PT_from_wells(well,layer,parameter,save,show):
	"""Genera graficas comparando la evolucion de parametros a lo largo del tiempo

	Parameters
	----------	  
	well : array
	  Nombre de pozo
	layer : str
	  Nombre de capa de parametro selecionado
	parameter : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{pozo}_{capa}_{parametro}_evol.png: archivo con direccion '../output/PT/images/evol/%s_%s_%s_evol.png'

	Note
	----
	Toma los datos de los archivo de entrada en ../input/drawdown e ../input/cooling, cualquier otro parametro solo ser graficado, sin comparacion alguna. La carpeta ../output/PT/evol/prev debe estar poblada con la capa y parametro correspondiente

	Examples
	--------
	>>> plot_compare_evol_PT_from_wells('AH-16A','B','T',save=True,show=False)
	"""

	if parameter  not in ["P","T","SG","SW","X(WAT1)","X(WAT2)","PCAP","DG","DW"]:
		print("Cant be printed, the parameter is  not register")
	elif parameter=="P":
		parameter_label="Pressure"
		parameter_unit="bar"
		file_real="../input/drawdown/%s_DD.dat"%well
		real_header='pressure'
	elif parameter=="T":
		parameter_label="Temperature"
		parameter_unit="C"
		file_real="../input/cooling/%s_C.dat"%well
		real_header='temperature'
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

	#Read file,  current calculated
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
				print(ref_date,"plus",str(times[n]),"wont be plot")

	
	#Read file, previous calculated 
	file="../output/PT/evol/prev/%s_PT_%s_evol.dat"%(well,layer)

	data_prev=pd.read_csv(file)

	times_prev=data_prev['TIME']

	values_prev=data_prev[parameter]

	dates_prev=[]
	values_to_plot_prev=[]
	for n in range(len(times_prev)):
		if float(times_prev[n])>0:
			try:
				dates_prev.append(ref_date+datetime.timedelta(days=int(times_prev[n])))
				if parameter!="P":
					values_to_plot_prev.append(values_prev[n])
				else:
					values_to_plot_prev.append(values_prev[n]/1E5)
			except OverflowError:
				print(ref_date,"plus",str(times_prev[n]),"wont be plot")

	
	#Read file, previous calculated 
	file="/home/erick/modelos_numericos/sostenibilidad_CGA_2020/resultadosAH25/escenario1_sin_ajuste.dat"
	data_1=pd.read_csv(file)

	time_1=data_1['TIME']

	values_1=data_1[parameter]

	dates_1=[]
	values_to_plot_prev_1=[]
	for n in range(len(time_1)):
		if float(time_1[n])>0:
			try:
				dates_1.append(ref_date+datetime.timedelta(days=int(time_1[n])))
				if parameter!="P":
					values_to_plot_prev_1.append(values_1[n])
				else:
					values_to_plot_prev_1.append(values_1[n]/1E5)
			except OverflowError:
				print(ref_date,"plus",str(time_1[n]),"wont be plot")

	#Read file, previous calculated 
	file="/home/erick/modelos_numericos/sostenibilidad_CGA_2020/resultadosAH25/escenario1_con_ajuste.dat"
	data_2=pd.read_csv(file)

	time_2=data_2['TIME']

	values_2=data_2[parameter]

	dates_2=[]
	values_to_plot_prev_2=[]
	for n in range(len(time_2)):
		if float(time_2[n])>0:
			try:
				dates_2.append(ref_date+datetime.timedelta(days=int(time_2[n])))
				if parameter!="P":
					values_to_plot_prev_2.append(values_2[n])
				else:
					values_to_plot_prev_2.append(values_2[n]/1E5)
			except OverflowError:
				print(ref_date,"plus",str(time_2[n]),"wont be plot")
	

	#Read file, previous calculated 
	file="/home/erick/modelos_numericos/sostenibilidad_CGA_2020/resultadosAH25/escenario2_sin_ajuste.dat"
	data_3=pd.read_csv(file)

	time_3=data_3['TIME']

	values_3=data_3[parameter]

	dates_3=[]
	values_to_plot_prev_3=[]
	for n in range(len(time_3)):
		if float(time_3[n])>0:
			try:
				dates_3.append(ref_date+datetime.timedelta(days=int(time_3[n])))
				if parameter!="P":
					values_to_plot_prev_3.append(values_3[n])
				else:
					values_to_plot_prev_3.append(values_3[n]/1E5)
			except OverflowError:
				print(ref_date,"plus",str(time_3[n]),"wont be plot")


	#Read file, previous calculated 
	file="/home/erick/modelos_numericos/sostenibilidad_CGA_2020/resultadosAH25/escenario2_con_ajuste.dat"
	data_4=pd.read_csv(file)

	time_4=data_4['TIME']

	values_4=data_4[parameter]

	dates_4=[]
	values_to_plot_prev_4=[]
	for n in range(len(time_4)):
		if float(time_4[n])>0:
			try:
				dates_4.append(ref_date+datetime.timedelta(days=int(time_4[n])))
				if parameter!="P":
					values_to_plot_prev_4.append(values_4[n])
				else:
					values_to_plot_prev_4.append(values_4[n]/1E5)
			except OverflowError:
				print(ref_date,"plus",str(time_4[n]),"wont be plot")
	
	#Read file, previous calculated 
	file="/home/erick/modelos_numericos/sostenibilidad_CGA_2020/resultadosAH25/escenario3_sin_ajuste.dat"
	data_5=pd.read_csv(file)

	time_5=data_5['TIME']

	values_5=data_5[parameter]

	dates_5=[]
	values_to_plot_prev_5=[]
	for n in range(len(time_5)):
		if float(time_5[n])>0:
			try:
				dates_5.append(ref_date+datetime.timedelta(days=int(time_5[n])))
				if parameter!="P":
					values_to_plot_prev_5.append(values_5[n])
				else:
					values_to_plot_prev_5.append(values_5[n]/1E5)
			except OverflowError:
				print(ref_date,"plus",str(time_5[n]),"wont be plot")


	file="../input/drawdown/p_res.csv"
	data_real_res=pd.read_csv(file,delimiter=';')
	dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%d/%m/%Y")
	dates_real_res=list(map(dates_func,data_real_res['date']))


	#knowing the masl
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	depth=pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%layer,conn)
	depth=depth.values[0][0]

	#Read file, real

	fig, ax = plt.subplots(figsize=(10,4))

	try:
		data_real=pd.read_csv(file_real)
		data_real.loc[data_real['TVD']==depth]['datetime']
		dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		dates_real=list(map(dates_func,data_real.loc[data_real['TVD']==depth]['datetime'].values))
		#ax.plot(dates_real,data_real.loc[data_real['TVD']==depth][real_header].values,'or',linewidth=1,ms=3,label='Real %s'%parameter_label)
	except (IOError,UnboundLocalError):
		print("No real data available") 

	#Plotting

	
	#ax.plot(dates,values_to_plot,'-ob',linewidth=1,ms=3,label='Current calculated %s'%parameter_label)
	#ax.plot(dates,values_to_plot,'-b',linewidth=1,ms=3,label='Escenario_3 con ajuste')
	#ax.plot(dates_prev,values_to_plot_prev,'-+k',linewidth=1,ms=3,label='Previous calculated %s'%parameter_label)
	ax.plot(dates_prev,values_to_plot_prev,'-k',linewidth=1,ms=3,label='Caso base')

	#Escenario 1
	ax.plot(dates_1,values_to_plot_prev_1,'-g',linewidth=1,ms=3,label='Escenario_1 ')
	#ax.plot(dates_2,values_to_plot_prev_2,'-+m',linewidth=1,ms=3,label='Escenario_1 con ajuste')
	ax.plot(dates_3,values_to_plot_prev_3,'-y',linewidth=1,ms=3,label='Escenario_2 ')
	#ax.plot(dates_4,values_to_plot_prev_4,'-+r',linewidth=1,ms=3,label='Escenario_2 con ajuste')
	ax.plot(dates_5,values_to_plot_prev_5,'-c',linewidth=1,ms=3,label='Escenario_3 ')
	ax.plot(dates_real_res,data_real_res['Pres'].values,'--',linewidth=1,ms=3,label='Presion de reservorio')

	ax.set_title("Well: %s at %s masl (layer %s)"%(well,depth,layer) ,fontsize=8)
	ax.set_xlabel("Time",fontsize = 8)
	ax.set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)

	ax.legend(loc="upper right")

	#Plotting formating
	xlims=[min(dates)-datetime.timedelta(days=365),ref_date+datetime.timedelta(days=100*365)]
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

	if save:
		fig.savefig('../calib/drawdown_cooling/images/%s_%s_%s_evol.png'%(well,layer,parameter)) 
	if show:
		plt.show()

def compare_evol_runs_PT(wells,db_path,layer,parameter):
	"""Genera un archivo pdf donde se compara la temperatura y presion real vs la calculada actual y previa

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Nombres de pozo
	layer : str
	  Nombre de capa
	parameter : str
	  Parametro a graficar, de forma que se muestre una evolucion correcta debe ser "P" o  "T"

	Returns
	-------
	pdf
		run_PT_evol_{date-time}.pdf: archivo con direccion ../calib/drawdown_cooling

	Note
	----
	La carpeta ../output/PT/evol/prev debe estar poblada con la capa y parametro 

	Examples
	--------
	>>> compare_evol_runs_PT(wells,db_path,layer='D',parameter='T')
	"""

	pdf_pages=PdfPages("../calib/drawdown_cooling/run_%s_evol"%parameter+str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))+".pdf")
	for well in sorted(wells):
		fig=plot_compare_evol_PT_from_wells(well,layer,parameter,save=True,show=False)
		pdf_pages.savefig(fig)

	d = pdf_pages.infodict()
	d['Title'] = '%s Calibration Model Plots'%field
	d['Author'] = 'O&MReservorios'
	d['Subject'] = 'Cooling/Drawdown'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()

	# Write the PDF document to the disk
	pdf_pages.close()

def plot_layer_from_PT_real_json(layer,method,ngridx,ngridy,save,show,print_points,print_eleme_name,variable_to_plot,print_mesh,levels,use_levels):
	"""Genera un corte en la capa especificada de la variable y fuente especificada

	Parameters
	----------	  
	layer : str
	  Nombre de capa
	method : str
	  Tipo de metodo para interpolacion
	ngridx : int
	  Numero de elementos en grid regular en direccion horizontal
	ngridy : int
	  Numero de elementos en grid regular en direccion vertical
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada
	print_points : bool
	  Imprime los centros de cada elemento
	print_eleme_name : bool
	  Imprime los nombres de los elementos
	variable_to_plot : str
	  Varibale a graficar: "P" o "T"
	source : str
	  Fuente de informacion, json generado a partir de "sav" o "t2"
	print_mesh : bool
	  Imprime la malla
	levels : array
	  Arreglo con valores para generar contornos
	use_levels : bool
	  Utiliza los valores dispuestos en levesl

	Other Parameters
	----------------
	bool
		color_levels_black : no rellena los contornos
	int
		fontsize_elements_label : tamanio de letra de pozos
	int
		fontsize_title : tamanio de titulo
	int
		fontsize_xy_label : tamanio de letra de titulos en xy
	int
		fontsize_ticks : tamanio de letra de coordenadas
	int
		fontsize_labels: tamanio de letra en contornos

	Returns
	-------
	image
		/real_layer_{layer}_{variable_to_plot}.png": archivo con direccion "../output/PT/images/real_layer

	Note
	----
	El archivo ../input/PT/PT_real_json.txt debe existir

	Examples
	--------
	>>> plot_layer_from_PT_real_json(layers[nv][0],'cubic',100,100,save=True,show=True,print_points=True,print_eleme_name=True,variable_to_plot="T",print_mesh=False,levels=levels,use_levels=False)
	"""

	fontsize_labels=6
	fontsize_ticks=6
	fontsize_xy_label=8
	fontsize_title=10
	fontsize_elements_label=6
	color_levels_black=False

	variable_to_plot_options={"T":[3,"Temperature [C]"],
					          "P":[4,"Pressure [bar]"]}

	index=variable_to_plot_options[variable_to_plot][0]

	file="../input/PT/PT_real_json.txt"

	if os.path.isfile(file):
		with open(file,"r") as f:
			data=json.load(f)
		element_name=[]
		x=[]
		y=[]
		z=[]
		variable=[]

		variable_min=100E8
		variable_max=0

		for elementx in data:
			if variable_max<data[elementx][index]:
				variable_max=data[elementx][index]

			if variable_min>data[elementx][index]:
				variable_min=data[elementx][index]

			if layer==elementx[-1]:
				x.append(data[elementx][0])
				y.append(data[elementx][1])
				z.append(data[elementx][2])
				variable.append(data[elementx][index])
				element_name.append(elementx)

		print(variable_max)
		if use_levels:
			variable_levels=levels
		else:
			variable_levels=np.linspace(variable_min,variable_max,num=10)

		xi = np.linspace(min(x), max(x), ngridx)
		yi = np.linspace(min(y), max(y), ngridy)

		#if method=='nearest':
		x = np.asarray(x, dtype=np.float32)
		y = np.asarray(y, dtype=np.float32)
		variable = np.asarray(variable, dtype=np.float32)

		zi = griddata((x, y), variable, (xi[None,:], yi[:,None]), method=method)

		fig=plt.figure(figsize=(10,8))

		ax1=fig.add_subplot(1,1,1)

		if variable_levels[0]!=variable_levels[-1]:
			if color_levels_black:
				contourax1=ax1.contour(xi,yi,zi,linewidths=1,cmap="jet")
			else:
				contourax1=ax1.contour(xi,yi,zi,linewidths=0.5,levels=variable_levels,colors="k")
				cntr3 = ax1.contourf(xi,yi,zi,cmap="jet",levels=variable_levels)
			ax1.clabel(contourax1, inline=1, fontsize=fontsize_labels,fmt='%10.0f',colors="k")
		else:
			contourax1=ax1.contour(xi,yi,zi,linewidths=0.5,colors='k')
			ax1.clabel(contourax1, inline=1, fontsize=fontsize_labels,fmt='%10.0f')
			cntr3 = ax1.contourf(xi,yi,zi,cmap="jet")

		if not color_levels_black:
			cbar=fig.colorbar(cntr3,ax=ax1)
			cbar.set_label("%s"%variable_to_plot_options[variable_to_plot][1])

		if print_points:
			ax1.plot(x,y,'ok',ms=1)

		if print_eleme_name:
			for n in range(len(element_name)):
				ax1.text(x[n],y[n], element_name[n], color='k',fontsize=fontsize_elements_label)

		if print_mesh:
			mesh_segment=open("../mesh/to_steinar/segmt","r")
			lines_x=[]
			lines_y=[]
			for line in mesh_segment:
				lines_x.append([float(line[0:15]),float(line[30:45])])
				lines_y.append([float(line[15:30]),float(line[45:60])])

			ax1.plot(np.array(lines_x).T,np.array(lines_y).T,'-k',linewidth=1,alpha=0.75)

		ax1.tick_params(axis='both', which='major', labelsize=fontsize_ticks,pad=1)
		ax1.set_ylabel('North [m]',fontsize =fontsize_xy_label)
		ax1.set_xlabel('East [m]',fontsize=fontsize_xy_label)
		ax1.set_title("Layer %s"%layer,fontsize=fontsize_title)

		if save:
			fig.savefig("../output/PT/images/real_layer/real_layer_%s_%s.png"%(layer,variable_to_plot)) 
		if show:
			plt.show()
	else:
		print("The PT_real_json file does not exist, run PT_real_to_json first")

def compare_PT_contours(layer,method,ngridx,ngridy,save,show,print_points,print_eleme_name,variable_to_plot,print_mesh,levels,use_levels,source,real_first):
	"""Genera  una imagen con los contornos de temperatura o presion donde se comparan los generados por los valores reales y calculados

	Parameters
	----------	  
	layer : str
	  Nombre de capa
	method : str
	  Tipo de metodo para interpolacion
	ngridx : int
	  Numero de elementos en grid regular en direccion horizontal
	ngridy : int
	  Numero de elementos en grid regular en direccion vertical
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada
	print_points : bool
	  Imprime los centros de cada elemento
	print_eleme_name : bool
	  Imprime los nombres de los elementos
	variable_to_plot : str
	  Varibale a graficar: "P" o "T"
	source : str
	  Fuente de informacion, json generado a partir de "sav" o "t2"
	levels : array
	  Arreglo con valores para generar contornos
	use_levels : bool
	  Utiliza los valores dispuestos en levesl
	print_mesh : bool
	  Imprime la malla
	real_first : bool
	  Coloca los contornos de la capa real primero

	Other Parameters
	----------------
	bool
		color_levels_black : no rellena los contornos
	int
		fontsize_elements_label : tamanio de letra de pozos
	int
		fontsize_title : tamanio de titulo
	int
		fontsize_xy_label : tamanio de letra de titulos en xy
	int
		fontsize_ticks : tamanio de letra de coordenadas
	int
		fontsize_labels: tamanio de letra en contornos
	float
		extent_X_min : limite horizontal menor de zoom
	float
		extent_X_max : limite horizontal mayor de zoom
	float
		extent_Y_min : limite vertical menor de zoom
	float
		extent_y_max : limite vertical mayor de zoom

	Returns
	-------
	image
		comparison_layer_{layer}_{variable_to_plot}.png: archivo con direccion ../calib/PT/images/layer_distribution/

	Note
	----
	El archivo ../input/PT/PT_real_json.txt debe existir y al menos  uno de los siguientes: PT_json_from_sav.txt y PT_json.txt

	Examples
	--------
	>>> levels=[100,150,170,180,200,220,230,250,260]
	>>> compare_PT_contours('D','linear',100,100,save=True,show=True,print_points=True,print_eleme_name=True,\
			variable_to_plot="T",print_mesh=False,levels=levels,use_levels=True,source="t2",real_first=True)
	"""

	fontsize_labels=6
	fontsize_ticks=6
	fontsize_xy_label=8
	fontsize_title=10
	fontsize_elements_label=4
	color_levels_black=False

	extent_X_min=411000
	extent_X_max=417000

	extent_Y_min=308000
	extent_Y_max=313000


	variables_to_plot_t2={"P":4,
						   "T":5}

	variables_to_plot_sav={"P":3,
	                       "T":4}

	if source=="sav":
		index_output=variables_to_plot_sav[variable_to_plot]
		file_output="../output/PT/json/PT_json_from_sav.txt"
	elif source=="t2":
		index_output=variables_to_plot_t2[variable_to_plot]
		file_output="../output/PT/json/PT_json.txt"


	variable_to_plot_options={"T":[3,"Temperature [C]"],
					          "P":[4,"Pressure [bar]"]}

	index=variable_to_plot_options[variable_to_plot][0]

	file="../input/PT/PT_real_json.txt"

	if os.path.isfile(file) and os.path.isfile(file_output):

		#Real data section
		with open(file,"r") as f:
			data=json.load(f)
		element_name=[]
		x=[]
		y=[]
		z=[]
		variable=[]

		variable_min=100E8
		variable_max=0

		for elementx in data:
			if variable_max<data[elementx][index]:
				variable_max=data[elementx][index]

			if variable_min>data[elementx][index]:
				variable_min=data[elementx][index]

			if layer==elementx[-1]:
				x.append(data[elementx][0])
				y.append(data[elementx][1])
				z.append(data[elementx][2])
				variable.append(data[elementx][index])
				element_name.append(elementx)

		if use_levels:
			variable_levels=levels
		else:
			variable_levels=np.linspace(variable_min,variable_max,num=10)

		xi = np.linspace(min(x), max(x), ngridx)
		yi = np.linspace(min(y), max(y), ngridy)
		zi = griddata((x, y), variable, (xi[None,:], yi[:,None]), method=method)


		#Calculated data section
		with open(file_output,"r") as f:
					data_output=json.load(f)

		element_name_output=[]
		x_output=[]
		y_output=[]
		z_output=[]
		variable_output=[]

		variable_min=100E8
		variable_max=0


		for elementx in data_output:
			if variable_max<data_output[elementx][index_output]:
				variable_max=data_output[elementx][index_output]

			if variable_min>data_output[elementx][index_output]:
				variable_min=data_output[elementx][index_output]

			if layer==elementx[0]:
				x_output.append(data_output[elementx][0])
				y_output.append(data_output[elementx][1])
				z_output.append(data_output[elementx][2])
				variable_output.append(data_output[elementx][index_output])
				element_name_output.append(elementx)

		xi_output = np.linspace(min(x_output), max(x_output), ngridx)
		yi_output = np.linspace(min(y_output), max(y_output), ngridy)

		zi_output = griddata((x_output, y_output), variable_output, (xi_output[None,:], yi_output[:,None]), method=method)

		fig=plt.figure(figsize=(10,8))

		ax1=fig.add_subplot(1,1,1)

		if variable_levels[0]!=variable_levels[-1]:
			if color_levels_black:
				contourax1=ax1.contour(xi,yi,zi,linewidths=1,colors="k",levels=variable_levels)
				ax1.clabel(contourax1, inline=True, fontsize=fontsize_labels,fmt='%10.0f',colors="k")

				contourax2=ax1.contour(xi_output,yi_output,zi_output,linewidths=1,colors="k",linestyles="--",levels=variable_levels)
				ax1.clabel(contourax2, inline=True, fontsize=fontsize_labels,fmt='%10.0f',colors="k")
				cntr3 = ax1.contourf(xi,yi,zi,cmap="jet",levels=variable_levels)
			else:
				contourax1=ax1.contour(xi,yi,zi,linewidths=0.5,levels=variable_levels,colors="k")
				ax1.clabel(contourax1, inline=True, fontsize=fontsize_labels,fmt='%10.0f',colors="k")

				contourax2=ax1.contour(xi_output,yi_output,zi_output,linewidths=0.5,levels=variable_levels,colors="k")
				ax1.clabel(contourax2, inline=True, fontsize=fontsize_labels,fmt='%10.0f',colors="k")

				if real_first:
					cntr4 = ax1.contourf(xi_output,yi_output,zi_output,cmap="jet",levels=variable_levels)
					cntr3 = ax1.contourf(xi,yi,zi,cmap="jet",levels=variable_levels)
				else:
					cntr3 = ax1.contourf(xi,yi,zi,cmap="jet",levels=variable_levels)
					cntr4 = ax1.contourf(xi_output,yi_output,zi_output,cmap="jet",levels=variable_levels)
					

		cbar=fig.colorbar(cntr3,ax=ax1)
		cbar.set_label("%s"%variable_to_plot_options[variable_to_plot][1])

		ax1.set_xlim([extent_X_min, extent_X_max])
		ax1.set_ylim([extent_Y_min, extent_Y_max])

		
		if print_points:
			ax1.plot(x,y,'ok',ms=1)

		if print_eleme_name:
			for n in range(len(element_name)):
				ax1.text(x[n],y[n], element_name[n], color='k',fontsize=fontsize_elements_label)

		if print_mesh:
			mesh_segment=open("../mesh/to_steinar/segmt","r")
			lines_x=[]
			lines_y=[]
			for line in mesh_segment:
				lines_x.append([float(line[0:15]),float(line[30:45])])
				lines_y.append([float(line[15:30]),float(line[45:60])])

			ax1.plot(np.array(lines_x).T,np.array(lines_y).T,'-k',linewidth=1,alpha=0.75)

		ax1.tick_params(axis='both', which='major', labelsize=fontsize_ticks,pad=1)
		ax1.set_ylabel('North [m]',fontsize =fontsize_xy_label)
		ax1.set_xlabel('East [m]',fontsize=fontsize_xy_label)
		ax1.set_title("Layer %s"%layer,fontsize=fontsize_title)

		if save:
			fig.savefig("../calib/PT/images/layer_distribution/comparison_layer_%s_%s.png"%(layer,variable_to_plot)) 
		if show:
			plt.show()

	else:
		print("The PT_real_json or PT_son file does not exist, run PT_real_to_json first")

def plot_compare_mh(well,block,source,save,show):
	"""Genera una grafica donde compara la evolucion de flujo y entalpia para el bloque asignado a la fuente de un pozo en particular

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Nombre de bloque, en general donde se ubica zona de alimentacion
	source : str
	  Nombre de fuente asociada a pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> plot_compare_mh('AH-1','DA110','SRC1',save=True,show=False)
	"""

	#Read file, current calculated
	file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)

	if os.path.isfile(file):
		data=pd.read_csv(file)
		#data.replace(0,np.nan, inplace=True)

		#Setting the time to plot
		
		times=data['TIME']

		dates=[]
		enthalpy=[]
		flow_rate=[]
		for n in range(len(times)):
			if float(times[n])>0:
				try:
					dates.append(input_data['ref_date']+datetime.timedelta(days=int(times[n])))
					#enthalpy.append(data['FF(AQ.)'][n]*100)
					enthalpy.append(data['ENTHALPY'][n]/1E3)
					flow_rate.append(data['GENERATION RATE'][n])
				except OverflowError:
					print(ref_date,"plus",str(times[n]),"wont be plot")
		
		#Real data

		fig, ax = plt.subplots(figsize=(10,4))

		ax.plot(dates,np.absolute(flow_rate),color=plot_conf_color['m'][1],\
			linestyle='--',ms=5,label='Calculated flow',marker=plot_conf_marker['current'][0],alpha=plot_conf_marker['current'][1])

		ax.set_title("Well: %s, block %s, source %s"%(well,block,source) ,fontsize=8)
		ax.set_xlabel("Time",fontsize = 8)
		ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)

		ax1 = ax.twinx()

		real_data=True
		try:
			data_real=pd.read_csv("../input/mh/%s_mh.dat"%well)
			data_real=data_real.set_index(['date-time'])
			data_real.index = pd.to_datetime(data_real.index)

			data_real['total_flow']=data_real['steam']+data_real['liquid']

			#Plotting

			
			#ax=data[['Flujo_total']].plot(figsize=(12,4),legend=False,linestyle="-")

			ax.plot(data_real.index,data_real['steam']+data_real['liquid'],\
				linestyle='-',color=plot_conf_color['m'][0],ms=3,label='Real',marker=plot_conf_marker['real'][0],alpha=plot_conf_marker['current'][1])
			ax1.plot(data_real.index,data_real['enthalpy'],'ob',\
				linestyle='None',color=plot_conf_color['h'][0],ms=3,label='Real',marker=plot_conf_marker['real'][0],alpha=plot_conf_marker['current'][1])
			
		except FileNotFoundError:
			real_data=False
			print("No real data for %s"%well)
			pass

		ax1.plot(dates,enthalpy,\
			linestyle='--',color=plot_conf_color['h'][1],ms=5,label='Calculated enthalpy',marker=plot_conf_marker['current'][0],alpha=plot_conf_marker['current'][1])

		ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)
		
		if real_data:
			plt.legend([ax.get_lines()[0],ax.get_lines()[1],ax1.get_lines()[0],ax1.get_lines()[1]],\
			                   ['Flow rate real','Flow rate calculated',\
			                    'Enthalpy real', 'Enthalpy calculated'],loc="upper right")
		else:
			plt.legend([ax.get_lines()[0],ax1.get_lines()[0]],\
			           ['Flow rate calculated','Enthalpy calculated'],loc="upper right")

		#Plotting formating
		#xlims=[min(dates)-datetime.timedelta(days=365),max(dates)+datetime.timedelta(days=365)]
		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')


		xlims=[input_data['ref_date']-datetime.timedelta(days=365),input_data['ref_date']++datetime.timedelta(days=60*365.25)]
		#ylims=[0,100]
		#ax1.set_ylim(ylims)

		ax.set_xlim(xlims)
		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.xaxis.set_major_formatter(years_fmt)

		#ax.xaxis.set_major_locator(years)
		#fig.autofmt_xdate()

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)

		if save:
			fig.savefig('../output/mh/images/%s_%s_%s_evol.png'%(well,block,source)) 
		if show:
			plt.show()
	else:
		print("There is not a file called %s, try running src_evol from output.py"%file)


def save_all_comparison_mh(db_path):
	"""Compara flujo y entalpia, real y calculada de todos los pozos

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/ para cada pozo

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> save_all_comparison_mh(db_path)
	"""
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource  WHERE source_nickname LIKE 'SRC%' ORDER BY source_nickname;",conn)

	for n in range(len(data_source)):
		well=data_source['well'][n]
		blockcorr=data_source['blockcorr'][n]
		source=data_source['source_nickname'][n]
		plot_compare_mh(well,blockcorr,source,save=True,show=False)

	conn.close()

def plot_compare_mh_previous(well,block,source,save,show):
	"""Genera  una imagen con los contornos de temperatura o presion donde se comparan los generados por los valores reales y calculados

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Bloque asociado fuente de  pozo
	source : str
	  Correlativo de SRC de pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada
	

	Returns
	-------
	image
		{pozo}_{bloque}_{fuente}_evol.png': archivo con direccion '../calib/mh/images

	Note
	----
	Los archivo correspondientes en las carpetas ../output/mh/txt/ y ../output/mh/txt/prev deben existir

	Examples
	--------
	>>> plot_compare_mh_previous('AH-1','DA110','SRC11',save=True,show=True)
	"""

	#Read file, current calculated
	file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)
	file_prev="../output/mh/txt/prev/%s_%s_%s_evol_mh.dat"%(well,block,source)

	if os.path.isfile(file):

		#Data current
		data=pd.read_csv(file)
		#data.replace(0,np.nan, inplace=True)

		#Setting the time to plot
		
		times=data['TIME']

		dates=[]
		enthalpy=[]
		flow_rate=[]
		for n in range(len(times)):
			if float(times[n])>0:
				try:
					dates.append(ref_date+datetime.timedelta(days=int(times[n])))
					enthalpy.append(data['ENTHALPY'][n]/1E3)
					flow_rate.append(data['GENERATION RATE'][n])
				except OverflowError:
					print(ref_date,"plus",str(times[n]),"wont be plot")


		#Data prev
		data_prev=pd.read_csv(file_prev)
		#data_prev.replace(0,np.nan, inplace=True)

		#Setting the time to plot
		
		times_prev=data_prev['TIME']

		dates_prev=[]
		enthalpy_prev=[]
		flow_rate_prev=[]
		for n in range(len(times_prev)):
			if float(times_prev[n])>0:
				try:
					dates_prev.append(ref_date+datetime.timedelta(days=int(times_prev[n])))
					enthalpy_prev.append(data_prev['ENTHALPY'][n]/1E3)
					flow_rate_prev.append(data_prev['GENERATION RATE'][n])
				except OverflowError:
					print(ref_date,"plus",str(times_prev[n]),"wont be plot")

		fig, ax = plt.subplots(figsize=(10,4))

		ax1 = ax.twinx()

		real_data=True
		try: 
			#Real data

			data_real=pd.read_csv("../input/mh/%s_mh.dat"%well)
			data_real=data_real.set_index(['date-time'])
			data_real.index = pd.to_datetime(data_real.index)

			data_real['total_flow']=data_real['steam']+data_real['liquid']


			ax.plot(data_real.index,data_real['steam']+data_real['liquid'],\
				linestyle='-',color=plot_conf_color['m'][0],ms=3,label='Real',marker=plot_conf_marker['real'][0],alpha=plot_conf_marker['current'][1])

			ax1.plot(data_real.index,data_real['enthalpy'],\
				linestyle='None',color=plot_conf_color['h'][0],ms=3,label='Real',marker=plot_conf_marker['real'][0],alpha=plot_conf_marker['current'][1])

		except FileNotFoundError:
			real_data=False
			print("No real data %s_%s_%s_evol_mh.dat"%(well,block,source))
			pass

		ax.plot(dates,np.absolute(flow_rate),color=plot_conf_color['m'][1],\
			linestyle='--',ms=5,label='Calculated current',marker=plot_conf_marker['current'][0],alpha=plot_conf_marker['current'][1])

		ax.plot(dates_prev,np.absolute(flow_rate_prev),color=plot_conf_color['m'][2],\
			linestyle='--',ms=5,label='Calculated previous',marker=plot_conf_marker['previous'][0],alpha=plot_conf_marker['previous'][1])

		ax.set_title("Well: %s, block %s, source %s"%(well,block,source) ,fontsize=8)
		ax.set_xlabel("Time",fontsize = 8)
		ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)


		ax1.plot(dates,enthalpy,\
			linestyle='--',color=plot_conf_color['h'][1],ms=5,label='Calculated',marker=plot_conf_marker['current'][0],alpha=plot_conf_marker['current'][1])

		ax1.plot(dates_prev,enthalpy_prev,\
			linestyle='--',color=plot_conf_color['h'][2],ms=5,label='Calculated',marker=plot_conf_marker['previous'][0],alpha=plot_conf_marker['previous'][1])

		ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)
		
		if not real_data:
			plt.legend([ax.get_lines()[0],ax.get_lines()[1],
				       ax1.get_lines()[0],ax1.get_lines()[1]],\
			                   ['Flow rate current','Flow rate previous',\
			                    'Enthalpy calculated','Enthalpy previous'],loc="upper right",fontsize=6)
		else:
			plt.legend([ax.get_lines()[0],ax.get_lines()[1],ax.get_lines()[2],
				       ax1.get_lines()[0],ax1.get_lines()[1],ax1.get_lines()[2]],\
			                   ['Flow rate real','Flow rate current','Flow rate previous',\
			                    'Enthalpy real', 'Enthalpy calculated','Enthalpy previous'],loc="upper right",fontsize=6)

		#Plotting formating
		xlims=[min(dates)-datetime.timedelta(days=365),ref_date+datetime.timedelta(days=60*365)]
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


		if save:
			fig.savefig('../calib/mh/images/%s_%s_%s_evol.png'%(well,block,source))
		if show:
			plt.show()
	else:
		print("There is not a file called %s or %s , try running src_evol from output.py"%(file,file_prev))
		return

def compare_mh_runs(field):
	"""Genera un archivo pdf donde compara la evolucion del flujo y la entalpia en las corridas TOUGH2 y se compara con los datos reales.

	Parameters
	----------	  
	field : str
	  Nombre de campo, tomado de model_conf

	Returns
	-------
	pdf
		run_mh_evol_{date-time}.pdf: archivo con direccion ../calib/mh/

	Note
	----
	Los archivo correspondientes en las carpetas ../output/mh/txt/ y ../output/mh/txt/prev deben existir

	Examples
	--------
	>>> compare_mh_runs(field)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource  WHERE source_nickname LIKE 'SRC%' ORDER BY source_nickname;",conn)

	pdf_pages=PdfPages("../calib/mh/run_mh_evol"+str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))+".pdf")

	for n in range(len(data_source)):
		well=data_source['well'][n]
		blockcorr=data_source['blockcorr'][n]
		source=data_source['source_nickname'][n]

		file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source)
		file_prev="../output/mh/txt/prev/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source)

		if os.path.isfile(file) and os.path.isfile(file_prev):
			fig=plot_compare_mh_previous(well,blockcorr,source,save=True,show=False)
			pdf_pages.savefig(fig)

	d = pdf_pages.infodict()
	d['Title'] = '%s Calibration Model Plots'%field
	d['Author'] = 'O&MReservorios'
	d['Subject'] = 'Cooling/Drawdown'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()
	pdf_pages.close()

	conn.close()

def vertical_cross_section_real(method,ngridx,ngridy,variable_to_plot,show_wells_3D):
	"""Genera un corte vertical en la trayectoria de una linea de una propiedad especificada

	Parameters
	----------	  
	method : str
	  Tipo de metodo para interpolacion
	ngridx : int
	  Numero de elementos en grid regular en direccion del corte
	ngridy : int
	  Numero de elementos en grid regular en direccion vertical
	show_wells_3D : bool
	  Muestra la geometria del pozo en 3D
	variable_to_plot : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW" para fuente t2 y "P" y "T" para sav

	Other Parameters
	----------------
	array
		x_points : coordenada x de linea
	array
		y_points : coordenada y de linea

	Returns
	-------
	image
		vertical_section_{varible_to_plot}.png: archivo con direccion '../output/PT/images/

	Note
	----
	La proyeccion de los pozos funciona correctamente cuando el pozo no se encuentre entre los vertices de la linea definida para el corte. El archivo PT_real_json.txt debe existir.

	Examples
	--------
	>>> vertical_cross_section_real(method='cubic',ngridx=100,ngridy=100,variable_to_plot="T",show_wells_3D=True)
	"""

	x_points=[571353,571376,572145]
	y_points=[262236,264877,266874]

	variables_to_plot_t2={"P":4,
						  "T":3}

	index=variables_to_plot_t2[variable_to_plot]
	file="../input/PT/PT_real_json.txt"

	if os.path.isfile(file):
		with open(file,"r") as f:
	  		data=json.load(f)
	  	
	variable_min=100E8
	variable_max=0

	#Creates an irregular grid with the form [[x,y,z],[x1,y1,z1]]
	irregular_grid=np.array([[0,0,0]])
	variable=np.array([])
	for elementx in data:
		if variable_max<data[elementx][index]:
			variable_max=data[elementx][index]

		if variable_min>data[elementx][index]:
			variable_min=data[elementx][index]

		irregular_grid=np.append(irregular_grid,[[data[elementx][0],data[elementx][1],data[elementx][2]]],axis=0)
		variable=np.append(variable,data[elementx][index])


	irregular_grid=irregular_grid[1:]
	variable=variable[0:]

	#Creates the points a long the lines
	x=np.array([])
	y=np.array([])
	
	for xy in range(len(x_points)):
		if xy < len(x_points)-1:
			xt=np.linspace(x_points[xy],x_points[xy+1]+(x_points[xy+1]-x_points[xy])/ngridx,num=ngridx)
			yt=np.linspace(y_points[xy],y_points[xy+1]+(y_points[xy+1]-y_points[xy])/ngridy,num=ngridy)
			x=np.append(x,xt)
			y=np.append(y,yt)

	#Calculates the distance of every point along the projection

	projection_req=np.array([0])
	for npr in range(1,len(x)):
		if npr==len(x)-1:
			break
		elif npr==1:
			delta_x_pr=(x_points[0]-x[0])**2
			delta_y_pr=(y_points[0]-y[0])**2
			prj_prox=(delta_y_pr+delta_x_pr)**0.5
		else:
			delta_x_pr=(x[npr+1]-x[npr])**2
			delta_y_pr=(y[npr+1]-y[npr])**2
			prj_prox=(delta_y_pr+delta_x_pr)**0.5
		projection_req=np.append(projection_req,prj_prox+projection_req[npr-1])

	ztop,zlabels, zmid,zbottom=t2r.vertical_layer(layers,z0_level)

	#Creates the regular  mesh in 3D along all the layers

	xi = np.linspace(min(x), max(x), ngridx)
	yi = np.linspace(min(y), max(y), ngridy)
	zi = np.array(zmid)

	proj_req=np.array([])
	z_req_proj=np.array([])

	for nprj in range(len(projection_req)):
		for nz in range(len(zi)):
			proj_req=np.append(proj_req,projection_req[nprj])
			z_req_proj=np.append(z_req_proj,zi[nz])

	request_points=np.array([[0,0,0]])
	x_req=np.array([])
	y_req=np.array([])
	z_req=np.array([])


	for nx in range(len(x)):
		for nz in range(len(zi)):
			request_points= np.append(request_points,[[x[nx],y[nx],zi[nz]]],axis=0)
			x_req=np.append(x_req,x[nx])
			y_req=np.append(y_req,y[nx])
			z_req=np.append(z_req,zi[nz])

	request_points=request_points[1:]

	requested_values = griddata(irregular_grid, variable, request_points)

	#Creates regular mesh on projection

	xi_pr = np.linspace(min(proj_req), max(proj_req), 1000)
	yi_pr = np.linspace(min(z_req_proj), max(z_req_proj), 1000)
	zi_pr = griddata((proj_req, z_req_proj), requested_values[:-len(zmid)], (xi_pr[None,:], yi_pr[:,None]))

	fig = plt.figure()

	#Plot projection
	
	ax = fig.add_subplot(211)

	ax.contour(xi_pr,yi_pr,zi_pr,15,linewidths=0.5,colors='k')
	cntr = ax.contourf(xi_pr,yi_pr,zi_pr,15,cmap="jet")
	ax.plot(proj_req,z_req_proj,'ok',ms=0.5)

	fig.colorbar(cntr,ax=ax)

	#Scatter 3D

	ax3D = fig.add_subplot(212, projection='3d')

	colorbar_source=ax3D.scatter3D(x_req,y_req,z_req,cmap='jet',c=requested_values)

	ax3D.set_xlabel('East [m]')
	ax3D.set_ylabel('North [m]')
	ax3D.set_zlabel('m.a.s.l.')
	fig.colorbar(colorbar_source, ax=ax3D)

	#Plot wells on 3D

	if show_wells_3D:
		conn=sqlite3.connect(db_path)
		c=conn.cursor()

		for name in sorted(wells):
			data_position=pd.read_sql_query("SELECT east,north,elevation FROM wells WHERE well='%s';"%name,conn)
			data=pd.read_sql_query("SELECT MeasuredDepth FROM survey WHERE well='%s' ORDER BY MeasuredDepth;"%name,conn)
			
			ax3D.text(data_position['east'][0], data_position['north'][0], data_position['elevation'][0], \
				      name, color='black',alpha=0.75,fontsize=8)

			x_real=[]
			y_real=[]
			z_real=[]

			for v in range(len(data['MeasuredDepth'])):
				xf,yf,zf=t2r.MD_to_TVD(name,data['MeasuredDepth'][v])
				x_real.append(float(xf))
				y_real.append(float(yf))
				z_real.append(float(zf))
		
			ax3D.plot3D(x_real, y_real, z_real,'-k',alpha=0.75)

		conn.close()

	if savefig:
		fig.savefig('../output/PT/images/vertical_section_%s_real.png'%variable_to_plot) 
	plt.show()

def plot_measured_vs_calculated(db_path,wells,inpath,savefig):
	"""Genera un corte vertical en la trayectoria de una linea de una propiedad especificada

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Arreglo con nombre de pozos
	inpath : str
	  Direccion de archivos de entrada de la salida TOUGH2
	savefig : bool
	  Almacena imagen generada

	Other Parameters
	----------------
	array
		x_points : coordenada x de linea
	array
		y_points : coordenada y de linea

	Returns
	-------
	image
		vertical_section_{varible_to_plot}.png: archivo con direccion '../output/PT/images/

	Note
	----
	Toma  los valores reales de la base de datos

	Examples
	--------
	>>> plot_measured_vs_calculated(db_path,wells,inpath="../output/PT/txt",savefig=True)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Define plot

	fig= plt.figure(figsize=(12, 24), dpi=300)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	T_real_all=[]
	P_real_all=[]
	T_calculated_all=[]
	P_calculated_all=[]

	for name in wells:

		if name[0] not in ['Z','X']:

			#Real data
			data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

			x_T,y_T,z_T,var_T=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

			x_P,y_P,z_P,var_P=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)

			#Model

			in_file="%s/%s_PT.dat"%(inpath,name)

			funcP_real=interpolate.interp1d(z_P,var_P)
			funcT_real=interpolate.interp1d(z_T,var_T)


			if os.path.isfile(in_file):

				data=pd.read_csv(in_file)
				data=data[1::] #Dont take the upper layer

				blk_num=data['ELEM'].values

				TVD_elem=[0 for n in range(len(blk_num))]
				TVD_elem_top=[0 for n in range(len(blk_num))]

				for n in range(len(blk_num)):
					TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
					TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])

				T_real_layers=[]
				P_real_layers=[]
				T_calc_elem=[]
				P_calc_elem=[]
				for n_TVD in range(len(TVD_elem)):
					try:
						T_real_layers.append(funcT_real(TVD_elem[n_TVD]))
						P_real_layers.append(funcP_real(TVD_elem[n_TVD]))
						T_calc_elem.append(data['T'][n_TVD+1])
						P_calc_elem.append(data['P'][n_TVD+1]/1E5)
					except ValueError:
						T_real_layers.append(np.nan)
						P_real_layers.append(np.nan)				
						T_calc_elem.append(np.nan)
						P_calc_elem.append(np.nan)

				T_real_all.extend(T_real_layers)
				P_real_all.extend(P_real_layers)
				T_calculated_all.extend(T_calc_elem)
				P_calculated_all.extend(P_calc_elem)
				axT.plot(T_real_layers,data['T'],'or',ms=1,alpha=0.5)
				axP.plot(P_real_layers,data['P']/1E5,'ob',ms=1,alpha=0.5)
	
	T_real_all=np.array(T_real_all)
	P_real_all=np.array(P_real_all)
	T_calculated_all=np.array(T_calculated_all)
	P_calculated_all=np.array(P_calculated_all)

	coef_T= np.polyfit(T_real_all[np.logical_not(np.isnan(T_real_all))],T_calculated_all[np.logical_not(np.isnan(T_calculated_all))],1)
	poly1d_fn_T = np.poly1d(coef_T) 

	coef_P=  np.polyfit(P_real_all[np.logical_not(np.isnan(P_real_all))],P_calculated_all[np.logical_not(np.isnan(P_calculated_all))],1)
	poly1d_fn_P = np.poly1d(coef_P) 

	print("Temperature, coeff",poly1d_fn_T)
	print("Pressure, coeff",poly1d_fn_P)

	fontsizex=4

	fontsize_layer=3

	axT.plot([min(T_real_all),max(T_real_all)], poly1d_fn_T([min(T_real_all),max(T_real_all)]), '--k',lw=0.3)

	axT.set_xlabel('Real temperature [C]',fontsize=fontsizex)

	axT.set_xlim([min(T_real_all),max(T_real_all)])
	axT.set_ylim([min(T_real_all),max(T_real_all)])

	axT.set_ylabel('Calculated temperarture [C]',fontsize = fontsizex)

	axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)
	
	axP.set_xlim([min(P_real_all),max(P_real_all)])

	axP.set_ylim([min(P_real_all),max(P_real_all)])

	axP.set_ylabel('Calculated pressure [bar]',fontsize = fontsizex)

	axP.set_xlabel('Real pressure [bar]',fontsize=fontsizex)

	axP.yaxis.set_label_coords(-0.1,0.5)

	axP.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

	fig.suptitle("Comparison real vs results", fontsize=fontsizex)

	plt.show()

	conn.close()

	if savefig:
		fig.savefig('../output/PT/images/PT_comparison.png') 

def real_flow(db_path):
	"""Genera una grafica donde compara la evolucion de flujo y entalpia para el bloque asignado a la fuente de un pozo en particular

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Nombre de bloque, en general donde se ubica zona de alimentacion
	source : str
	  Nombre de fuente asociada a pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> real_flow(db_path)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource  WHERE well LIKE 'AH%' OR well LIKE 'CH%'  OR well LIKE 'Z%'  OR well LIKE 'X%' ORDER BY source_nickname;",conn)
	conn.close()

	times_days=[]
	dates=[]

	subprocess.call(['./shell/extract_times.sh'])
	data_times=pd.read_csv('times_temp')
	times=data_times['TIME']
	for days in times:
		if days>0 and days <365*100:
			dates.append(ref_date+datetime.timedelta(days=days))
			times_days.append(days)

	flow_rate=[0.0 for nx in range(len(times_days))]
	flow_extract=[0.0 for nx in range(len(times_days))]
	steam_flow=[0.0 for nx in range(len(times_days))]
	liquid_flow=[0.0 for nx in range(len(times_days))]

	for ndays in range(len(times_days)):

		for n in range(len(data_source)):
			well=data_source['well'][n]
			blockcorr=data_source['blockcorr'][n]
			source=data_source['source_nickname'][n]

			#Read file, current calculated
			file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source)


			if os.path.isfile(file):
				data=pd.read_csv(file)
				print(file)
				for times in range(len(data['TIME'])):
					if data['TIME'][times]==times_days[ndays]:
						flow_rate[ndays]+=-data['GENERATION RATE'][times]
						if data['GENERATION RATE'][times]<0:
							flow_extract[ndays]+=-data['GENERATION RATE'][times]
							steam_flow[ndays]+=-data['GENERATION RATE'][times]*data['FF(GAS)'][times]
							liquid_flow[ndays]+=-data['GENERATION RATE'][times]*data['FF(AQ.)'][times]

	os.remove("times_temp")

	fig, ax = plt.subplots(figsize=(10,4))

	ax.plot(dates,flow_rate,'-',lw=1,ms=3,label='Flujo neto')
	ax.plot(dates,flow_extract,'-',lw=1,ms=3,label='Flujo extraido')
	#ax.plot(dates,steam_flow,'--+m',lw=1,ms=3,label='Calculated steam flow')
	#ax.plot(dates,liquid_flow,'--+g',lw=1,ms=3,label='Calculated liquid flow')

	ax.set_xlabel('Time',fontsize=10)
	ax.set_ylabel('Flow rate [kg/s]',fontsize=10)

	ax.set_title("Simulated flow rate from feedzone vs real flow rate",fontsize=10)
	ax.set_ylim([0,1500])

	fig.savefig('../report/images/real_flow.png') 
	plt.legend()
	plt.show()

def mh_block_result(well_to_plot,block_to_plot,source_to_plot,save,plots_per_page):
	"""Genera  una imagen con los contornos de temperatura o presion donde se comparan los generados por los valores reales y el ultimo calculado

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Bloque asociado fuente de  pozo
	source : str
	  Correlativo de SRC de pozo
	save : bool
	  Almacaena la grafica generada


	Returns
	-------
	image
		{pozo}_{bloque}_{fuente}_evol.png': archivo con direccion '../report/images/mh

	Note
	----
	Los archivo correspondientes en las carpetas ../output/mh/txt/ deben existir

	Examples
	--------
	>>> plot_compare_mh_previous('AH-1','DA110','SRC11',save=True,show=True)
	"""

	fig, ax = plt.subplots(plots_per_page,figsize=(8.5,11))
	for nv in range(plots_per_page):
		try: 

			#Read file, current calculated
			file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well_to_plot[nv],block_to_plot[nv],source_to_plot[nv])
			well=well_to_plot[nv]
			block=block_to_plot[nv]
			source=source_to_plot[nv]

			if os.path.isfile(file):

				#Data current
				data=pd.read_csv(file)

				#Setting the time to plot
				
				times=data['TIME']

				dates=[]
				enthalpy=[]
				flow_rate=[]
				data['ENTHALPY'].replace(0.0, np.nan, inplace=True)
				for n in range(len(times)):
					if float(times[n])>0:
						try:
							dates.append(ref_date+datetime.timedelta(days=int(times[n])))
							enthalpy.append(data['ENTHALPY'][n]/1E3)
							flow_rate.append(data['GENERATION RATE'][n])
						except OverflowError:
							print(ref_date,"plus",str(times[n]),"wont be plot")


				#Real data
				data_real=pd.read_csv("../input/mh/%s_mh.dat"%well)
				data_real=data_real.set_index(['date-time'])
				data_real.index = pd.to_datetime(data_real.index)
				data_real['total_flow']=data_real['steam']+data_real['liquid']

				#Plotting

				ax[nv].plot(data_real.index,data_real['steam']+data_real['liquid'],\
					linestyle=None,color=plot_conf_color['m'][0],ms=3,label='Real',marker=plot_conf_marker['real'][0],alpha=plot_conf_marker['current'][1])

				ax[nv].plot(dates,np.absolute(flow_rate),color=plot_conf_color['m'][1],\
					linestyle='--',ms=5,label='Calculated current',marker=plot_conf_marker['current'][0],alpha=plot_conf_marker['current'][1])

				ax[nv].set_title("Well: %s, block %s, source %s"%(well,block,source) ,fontsize=8)

				ax[nv].set_ylabel('Flow rate [kg/s]',fontsize = 8)

				ax1 = ax[nv].twinx()

				ax1.plot(data_real.index,data_real['enthalpy'],\
					linestyle='None',color=plot_conf_color['h'][0],ms=3,label='Real',marker=plot_conf_marker['real'][0],alpha=plot_conf_marker['current'][1])

				ax1.plot(dates,enthalpy,\
					linestyle='None',color=plot_conf_color['h'][1],ms=4,label='Calculated',marker=plot_conf_marker['current'][0],alpha=plot_conf_marker['current'][1])

				ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)
				

				plt.legend([ax[nv].get_lines()[0],ax[nv].get_lines()[1],
					       ax1.get_lines()[0],ax1.get_lines()[1]],\
				                   ['Flow rate real','Simulated flow rate',\
				                    'Real enthalpy', 'Calculated Enthalpy'],loc="upper right",fontsize=6)

				#Plotting formating
				xlims=[min(dates)-datetime.timedelta(days=365),ref_date+datetime.timedelta(days=45*365)]
				ax[nv].format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

				years = mdates.YearLocator()
				years_fmt = mdates.DateFormatter('%Y')

				ax[nv].set_xlim(xlims)
				ax1.set_ylim(bottom=800)
				ax[nv].xaxis.set_major_formatter(years_fmt)


				#Grid style
				ax[nv].yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
				ax[nv].xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
				ax[nv].grid(True)
			else:
				ax[nv].set_title("Well: %s, block %s, source %s"%(well,block,source) ,fontsize=8)
				print("There is not a file called %s, try running src_evol from output.py"%(file))
				pass
			if nv+1==plots_per_page or nv==(len(well_to_plot)-1):
				ax[nv].set_xlabel("Time",fontsize = 8)
		except IndexError:
			ax[nv].axis('off')

	if save:
		fig.savefig('../report/images/mh/mh_result_%s.png'%(well_to_plot))

def mh_output_pdf():
	"""Genera un archivo pdf donde compara la evolucion del flujo y la entalpia en las corridas TOUGH2, con los datos reales.

	Parameters
	----------	  
	field : str
	  Nombre de campo, tomado de model_conf

	Returns
	-------
	pdf
		mh_results.pdf: archivo con direccion ../report/pdf/

	Note
	----
	Los archivo correspondientes en la carpeta ../output/mh/txt/  deben existir

	Examples
	--------
	>>> compare_mh_runs(field)
	"""

	prod=['SRC10','SRC17','SRC19','SRC21','SRC22','SRC24','SRC25',\
	'SRC26','SRC27','SRC28','SRC30','SRC31','SRC32','SRC36','SRC37','SRC39','SRC40','SRC41','SRC42','SRC44','SRC45','SRC46','SRC50','SRC52']
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource  WHERE well LIKE 'AH%' OR well LIKE 'C%' OR well LIKE 'X%' OR well LIKE 'Z%' ORDER BY source_nickname;",conn)

	pdf_pages=PdfPages("../report/pdf/mh_results_compare.pdf")

	plots_per_page=3
	cnt=0
	well_to_plot=[]
	block_to_plot=[]
	source_to_plot=[]
	for n in range(len(data_source)):
		file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(data_source['well'][n],data_source['blockcorr'][n],data_source['source_nickname'][n])
		
		if os.path.isfile(file) and data_source['well'][n] not in ['AH-11','AH-12'] and data_source['source_nickname'][n] in prod:
			well_to_plot.append(data_source['well'][n])
			block_to_plot.append(data_source['blockcorr'][n])
			source_to_plot.append(data_source['source_nickname'][n])
			cnt+=1	
			if (cnt)%plots_per_page==0 or (len(data_source)-(n+1))<plots_per_page:
				fig=mh_block_result(well_to_plot,block_to_plot,source_to_plot,True,plots_per_page)
				pdf_pages.savefig(fig)
				well_to_plot=[]
				block_to_plot=[]
				source_to_plot=[]
				cnt=0
		else:
			print(file)

	d = pdf_pages.infodict()
	d['Title'] = '%s Calibration Model Plots'%field
	d['Author'] = 'O&MReservorios'
	d['Subject'] = 'Flowing enthalpy'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()
	pdf_pages.close()

	conn.close()
	return

def PT_block_evol_output(well_to_plot,layer,parameter,show,plots_per_page):
	"""Genera graficas comparando la evolucion de parametros a lo largo del tiempo

	Parameters
	----------	  
	well : array
	  Nombre de pozo
	layer : str
	  Nombre de capa de parametro selecionado
	parameter : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{pozo}_{capa}_{parametro}_evol.png: archivo con direccion '../output/PT/images/evol/%s_%s_%s_evol.png'

	Note
	----
	Toma los datos de los archivo de entrada en ../input/drawdown e ../input/cooling, cualquier otro parametro solo ser graficado, sin comparacion alguna. La carpeta ../output/PT/evol/prev debe estar poblada con la capa y parametro correspondiente

	Examples
	--------
	>>> PT_block_evol_output('AH-16A','B','T',save=True,show=False,3)
	"""

	#knowing the masl
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	depth=pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%layer,conn)
	depth=depth.values[0][0]
	conn.close()

	fig, ax = plt.subplots(plots_per_page,figsize=(8.5,11))

	for nv in range(len(well_to_plot)):


		if parameter  not in ["P","T","SG","SW","X(WAT1)","X(WAT2)","PCAP","DG","DW"]:
			print("Cant be printed, the parameter is  not register")
		elif parameter=="P":
			parameter_label="Pressure"
			parameter_unit="bar"
			file_real="../input/drawdown/%s_DD.dat"%well_to_plot[nv]
			real_header='pressure'
		elif parameter=="T":
			parameter_label="Temperature"
			parameter_unit="C"
			file_real="../input/cooling/%s_C.dat"%well_to_plot[nv]
			real_header='temperature'
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

		#Read file,  current calculated
		file="../output/PT/evol/%s_PT_%s_evol.dat"%(well_to_plot[nv],layer)
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
					print(ref_date,"plus",str(times[n]),"wont be plot")



		#Read file, real

		try:
			data_real=pd.read_csv(file_real)
			data_real.loc[data_real['TVD']==depth]['datetime']
			dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
			dates_real=list(map(dates_func,data_real.loc[data_real['TVD']==depth]['datetime'].values))
			ax[nv].plot(dates_real,data_real.loc[data_real['TVD']==depth][real_header].values,'or',linewidth=1,ms=3,label='Real %s'%parameter_label)
		except (IOError,UnboundLocalError):
			print("No real data available") 

		#Plotting

		ax[nv].plot(dates,values_to_plot,'-ob',linewidth=1,ms=2,label='Current calculated %s'%parameter_label)
		ax[nv].set_title("Well: %s at %s masl (layer %s)"%(well_to_plot[nv],depth,layer) ,fontsize=8)
		if nv+1==plots_per_page:
			ax[nv].set_xlabel("Time",fontsize = 8)
		ax[nv].set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)

		if parameter=='P':
			ax[nv].legend(loc="upper right",fontsize=6)
		else:
			ax[nv].legend(loc="lower left",fontsize=6)

		#Plotting formating
		xlims=[min(dates)-datetime.timedelta(days=365),ref_date+datetime.timedelta(days=60*365)]
		ax[nv].format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax[nv].set_xlim(xlims)
		ax[nv].xaxis.set_major_formatter(years_fmt)

		#Grid style
		ax[nv].yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax[nv].xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax[nv].grid(True)
	if show:
		plt.show()

def PT_evol_output(wells,db_path,layer,parameter,plots_per_page):
	"""Genera un archivo pdf de salida (presentacion) donde se compara la temperatura y presion real vs la calculada actual y previa

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Nombres de pozo
	layer : str
	  Nombre de capa
	parameter : str
	  Parametro a graficar, de forma que se muestre una evolucion correcta debe ser "P" o  "T"
	plots_per_page : int
	  Numero de graficos por pagina

	Returns
	-------
	pdf
		run_PT_evol_{date-time}.pdf: archivo con direccion ../calib/drawdown_cooling

	Note
	----
	La carpeta ../output/PT/evol/prev debe estar poblada con la capa y parametro 

	Examples
	--------
	>>> compare_evol_runs_PT(wells,db_path,layer='D',parameter='T')
	"""
	
	pdf_pages=PdfPages("../report/pdf/PT_results_compare_%s_%s.pdf"%(parameter,layer))

	cnt=0
	plots_per_page=3
	well_to_plot=[]

	for n in range(len(wells)):
		well_to_plot.append(wells[n])
		cnt+=1
		if (cnt)%plots_per_page==0 or (len(wells)-(n+1))<plots_per_page:
			print(well_to_plot)
			fig=PT_block_evol_output(well_to_plot,layer,parameter,False,plots_per_page)
			pdf_pages.savefig(fig)
			cnt=0
			well_to_plot=[]

	d = pdf_pages.infodict()
	d['Title'] = '%s Output plots'%field
	d['Author'] = 'O&MReservorios'
	d['Subject'] = 'Cooling/Drawdown'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()

	# Write the PDF document to the disk
	pdf_pages.close()

def PT_block_evol_output_many(well_to_plot,layer,parameter,show,plots_per_page,location_dictionary):
	"""Genera graficas comparando la evolucion de parametros a lo largo del tiempo

	Parameters
	----------	  
	well : array
	  Nombre de pozo
	layer : str
	  Nombre de capa de parametro selecionado
	parameter : str
	  Varibale a graficar: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{pozo}_{capa}_{parametro}_evol.png: archivo con direccion '../output/PT/images/evol/%s_%s_%s_evol.png'

	Note
	----
	Toma los datos de los archivo de entrada en ../input/drawdown e ../input/cooling, cualquier otro parametro solo ser graficado, sin comparacion alguna. La carpeta ../output/PT/evol/prev debe estar poblada con la capa y parametro correspondiente

	Examples
	--------
	>>> PT_block_evol_output('AH-16A','B','T',save=True,show=False,3)
	"""

	#knowing the masl
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	depth=pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%layer,conn)
	depth=depth.values[0][0]
	conn.close()

	fig, ax = plt.subplots(plots_per_page,figsize=(8.5,11))

	for nv in range(len(well_to_plot)):
		if parameter  not in ["P","T","SG","SW","X(WAT1)","X(WAT2)","PCAP","DG","DW"]:
			print("Cant be printed, the parameter is  not register")
		elif parameter=="P":
			parameter_label="Pressure"
			parameter_unit="bar"
			file_real="../input/drawdown/%s_DD.dat"%well_to_plot[nv]
			real_header='pressure'
		elif parameter=="T":
			parameter_label="Temperature"
			parameter_unit="C"
			file_real="../input/cooling/%s_C.dat"%well_to_plot[nv]
			real_header='temperature'
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


		#Read file, real

		try:
			data_real=pd.read_csv(file_real)
			data_real.loc[data_real['TVD']==depth]['datetime']
			dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
			dates_real=list(map(dates_func,data_real.loc[data_real['TVD']==depth]['datetime'].values))
			ax[nv].plot(dates_real,data_real.loc[data_real['TVD']==depth][real_header].values,'or',linewidth=1,ms=3,label='Real %s'%parameter_label)
		except (IOError,UnboundLocalError):
			print("No real data available") 


		for scenario in location_dictionary:

			#Read file,  current calculated
			file="%s/%s_PT_%s_evol.dat"%(location_dictionary[scenario],well_to_plot[nv],layer)
			try:
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
							print(ref_date,"plus",str(times[n]),"wont be plot")

				#Plotting
				ax[nv].plot(dates,values_to_plot,'-',linewidth=1,ms=2,label='%s %s'%(scenario,parameter_label))
				ax[nv].set_title("Well: %s at %s masl (layer %s)"%(well_to_plot[nv].replace("X","").replace("Z",""),depth,layer) ,fontsize=8)
				if nv+1==plots_per_page:
					ax[nv].set_xlabel("Time",fontsize = 8)
				ax[nv].set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)
			except FileNotFoundError:
				print("for %s there is not information %s"%(scenario,file))

		if parameter=='P':
			ax[nv].legend(loc="upper right",fontsize=6)
		else:
			ax[nv].legend(loc="lower left",fontsize=6)

		#Plotting formating
		xlims=[min(dates)-datetime.timedelta(days=365),ref_date+datetime.timedelta(days=100*365)]
		ax[nv].format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax[nv].set_xlim(xlims)
		ax[nv].xaxis.set_major_formatter(years_fmt)

		#Grid style
		ax[nv].yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax[nv].xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax[nv].grid(True)
	fig.savefig('../report/images/PT/%s_%s_%s.png'%(well_to_plot,parameter,layer))

def PT_evol_many_ouputs(wells,db_path,layer,parameter,plots_per_page,location_dictionary):
	"""Genera un archivo pdf de salida (presentacion) donde se compara la temperatura y presion real vs la calculada actual y previa

	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Nombres de pozo
	layer : str
	  Nombre de capa
	parameter : str
	  Parametro a graficar, de forma que se muestre una evolucion correcta debe ser "P" o  "T"
	plots_per_page : int
	  Numero de graficos por pagina

	Returns
	-------
	pdf
		run_PT_evol_{date-time}.pdf: archivo con direccion ../calib/drawdown_cooling

	Note
	----
	La carpeta ../output/PT/evol/prev debe estar poblada con la capa y parametro 

	Examples
	--------
	>>> compare_evol_runs_PT(wells,db_path,layer='D',parameter='T')
	"""
	
	location_dictionary={'Base':'../../20200712b/output/PT/evol',
						 'Escenario 1':'../../escenario1_sin_ajuste/output/PT/evol',
						 'Escenario 2':'../../escenario2_sin_ajuste/output/PT/evol',
						 'Escenario 3':'../../escenario3_sin_ajuste/output/PT/evol'}

	pdf_pages=PdfPages("../report/pdf/PT_results_compare_%s_%s_many.pdf"%(parameter,layer))

	cnt=0
	plots_per_page=3
	well_to_plot=[]

	for n in range(len(wells)):
		well_to_plot.append(wells[n])
		cnt+=1
		if (cnt)%plots_per_page==0 or (len(wells)-(n+1))<plots_per_page:
			print(well_to_plot)
			fig=PT_block_evol_output_many(well_to_plot,layer,parameter,False,plots_per_page,location_dictionary)

			pdf_pages.savefig(fig)
			cnt=0
			well_to_plot=[]

	d = pdf_pages.infodict()
	d['Title'] = '%s Output plots'%field
	d['Author'] = 'O&MReservorios'
	d['Subject'] = 'Cooling/Drawdown'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()

	# Write the PDF document to the disk
	pdf_pages.close()


#compare_mh_runs(field)

"""
name='AH-34'

inpath="../output/PT/txt"

plot_compare_one(db_path,name,inpath,savefig=True)
"""

"""
typePT='T'
image_save_all_plots(db_path,wells,typePT) #typePT, could be T or P
"""

#compare_runs_PT(wells,db_path)

#vertical_cross_section(method='cubic',ngridx=100,ngridy=100,variable_to_plot="T",source="sav",show_wells_3D=True,print_point=False,savefig=False)



#save_all_PT_evol_from_layer(wells,layer='D',parameter='T')



"""
levels=[100,150,170,180,200,220,230,250,260]
compare_PT_contours('D','linear',100,100,save=True,show=True,print_points=True,print_eleme_name=True,\
			variable_to_plot="T",print_mesh=False,levels=levels,use_levels=True,source="t2",real_first=True)

"""




"""
Chinameca
"""

#vertical_cross_sec#tion_real(method='cubic',ngridx=100,ngridy=100,variable_to_plot="T",show_wells_3D=True)

"""
levels=[150,170,180,200,220,230,250,260]

for nv in layers:
	plot_layer_from_PT_real_json(layers[nv][0],'cubic',100,100,save=True,show=True,print_points=True,print_eleme_name=True,variable_to_plot="T",print_mesh=False,levels=levels,use_levels=True)

"""
"""
plot_layer_from_json('D','linear',1000,1000,save=True,show=True,print_points=False,print_eleme_name=False,\
			variable_to_plot="P",source="t2",print_mesh=False,print_well=True)
"""

#compare_runs_PT(wells,db_path)

#plot_all_layer()
#plot_PT_evol_block_in_wells('CHI-6A',layer='E',parameter='T',save=True,show=True)

#save_all_comparison_mh(db_path)


#Sostenibilidad CGA

#plot_compare_evol_PT_from_wells('AH-17','E','P',save=True,show=True)



#plot_compare_evol_PT_from_wells('AH-35A','E','P',save=True,show=True)

#plot_compare_PT_curr_prev(db_path,'AH-22',"../output/PT/txt","../output/PT/txt/prev",show=True)




#real_flow(db_path)

#plot_compare_mh('AH-16A','JA118','SRC17',save=True,show=True)

#plot_compare_mh('AH-1','DA110','SRC10',save=True,show=True)

#plot_compare_mh('AH-17','JA119','SRC19',save=True,show=True)

#plot_compare_mh_previous('AH-1','DA110','SRC10',save=True,show=True)

#plot_compare_mh_previous('AH-16A','JA118','SRC17',save=True,show=True)

#plot_compare_mh_previous('CH-9A','MA161','SRC62',save=True,show=True)

#plot_compare_mh_previous('AH-17','JA119','SRC19',save=True,show=True)

#plot_compare_PT_curr_prev(db_path,'AH-1',"../output/PT/txt","../output/PT/txt/prev",show=True)

#plot_compare_evol_PT_from_wells('AH-1','G','P',save=True,show=True)

#plot_compare_evol_PT_from_wells('AH-17','E','P',save=True,show=True)

#plot_compare_evol_PT_from_wells('AH-25','E','P',save=True,show=True)

#plot_compare_evol_PT_from_wells('AH-35A','E','P',save=True,show=True)

#plot_compare_evol_PT_from_wells('AH-4BIS','C','P',save=True,show=True)

#plot_compare_evol_PT_from_wells('AH-6','E','P',save=True,show=True)

#plot_layer_from_json('E','cubic',100,100,save=True,show=True,print_points=True,print_eleme_name=False,\
#			variable_to_plot="T",source="sav",print_mesh=False,print_well=True)

#levels=[150,170,180,200,220,230,250,260]
#plot_layer_from_PT_real_json('E','cubic',100,100,save=True,show=True,print_points=True,print_eleme_name=True,variable_to_plot="T",print_mesh=False,levels=levels,use_levels=True)

#plot_compare_mh_previous('AH-1','DA110','SRC11',save=True,show=True)

#image_save_all_plots(db_path,wells,'T')

#plot_PT_evol_block_in_wells('AH-25',layer='E',parameter='P',save=True,show=True)



#compare_runs_PT(wells,db_path,title)

#compare_evol_runs_PT(wells,db_path,'E','P')

#save_all_comparison_mh(db_path)

#compare_mh_runs(field)

#mh_output_pdf()

#real_flow(db_path)

#plot_measured_vs_calculated(db_path,wells,inpath="../output/PT/txt",savefig=True)

#PT_evol_output(wells,db_path,'E','P',3)

location_dictionary={'Escenario 1':'../../../escenario1_sin_ajuste/output/PT/evol/',
					 'Escenario 2':'../../../escenario2_sin_ajuste/output/PT/evol/',
					 'Escenario 3':'../../../escenario3_sin_ajuste/output/PT/evol/'}

#PT_evol_many_ouputs(wells,db_path,'E','P',3,location_dictionary)

#plot_compare_evol_PT_from_wells('AH-25','E','P',save=True,show=True)

#real_flow(db_path)

#plot_compare_one(well='AH-34',savefig=True)

#image_save_all_plots(typePT='T')

#plot_layer_from_json('K','linear',1000,1000,save=True,show=True,print_points=True,print_eleme_name=False,variable_to_plot="T",source="t2",print_mesh=False,print_well=False,use_lim=True)

#plot_all_layer()

#plot_compare_PT_curr_prev(well='AH-34A',show=True)

#compare_runs_PT()