#from model_conf import *
import numpy as np
import pyamesh as pya
import shutil
import os
import matplotlib.pyplot as plt

def vertical_layer(layers,z0_level):

	"""Return:
	   Top masl of every layer
	   Namer of every the layer
	   Middle masl of every layer
	"""

	y_layers=[]
	y_layers_ticks_labes=[]
	y_layers_ticks_labes_position=[]

	depth=0
	cnt=0
	for keys in sorted(layers):
		depth+=layers[keys][1]
		z_bottom=z0_level-depth
		if cnt==0:
			z_top=z0_level
		else:
			z_top+=-layers[last_key][1]
		last_key=keys
		cnt+=1
		y_layers.append(z_top)

		layers[keys].extend((z_top,z_bottom))
		y_layers_ticks_labes.append(layers[keys][0])
		y_layers_ticks_labes_position.append((z_top+z_bottom)*0.5)

	return y_layers,y_layers_ticks_labes, y_layers_ticks_labes_position

def mesh_creation_func(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers,layer_to_plot,x_space,y_space,radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,plot_names,plot_centers,z0_level,\
			mesh_creation,plot_layer,to_steinar,to_GIS,plot_all_GIS):
	
	layers_thick=map(float,np.array(layers.values())[:][:,1])

	blocks=pya.py2amesh(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers_thick,layer_to_plot,x_space,y_space,radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,plot_names,plot_centers,z0_level,plot_all_GIS)
	if mesh_creation==1:

		blocks.input_file_to_amesh()

		if plot_layer==1:
			blocks.plot_voronoi()
		if to_steinar==1:
			blocks.to_steinar()
		if to_GIS==1:
			blocks.to_GIS()

	if mesh_creation!=1 and plot_layer==1:
		blocks.plot_voronoi()
	if mesh_creation!=1 and to_steinar==1:
		blocks.to_steinar()
	if mesh_creation!=1 and to_GIS==1:
		blocks.to_GIS()

	return None

def empty_mesh():
	"""
	Empty all the folder related with the mesh
	"""
	folders=['../mesh/to_steinar','../mesh/from_amesh','../mesh/GIS']
	for folder in folders:
		for file in os.listdir(folder):
			file_path=os.path.join(folder,file)
			os.remove(file_path)

def plot_vertical_layer_distribution(layers,z0_level):

	y_layers,y_layers_ticks_labes, y_layers_ticks_labes_position=vertical_layer(layers,z0_level)

	plt.rcParams["font.family"] = "Times New Roman"

	fig=plt.figure(figsize=(2.5, 10), dpi=100)
	ax=fig.add_subplot(111)

	font_title_size=12
	fontsizey_layers=10
	fontsizex=8

	y_layer_plot=y_layers
	x_layer_plot=[100]*len(y_layers)

	ax.plot(x_layer_plot,y_layer_plot,'-r',alpha=0)
	Depth_lims=[-2150,1000]

	ax.set_ylim(Depth_lims)
	ax.set_xlim([95,105])

	ax.set_ylabel('m.a.s.l.',fontsize = fontsizey_layers)
	ax.xaxis.tick_top()
	ax.tick_params(axis='x',which='both',length=0,labeltop=False)
	ax.title.set_position([0.5,1.05])
	ax.xaxis.set_label_coords(0.5,1.15)
	ax.yaxis.set_label_coords(-0.2,0.5)
	ax.tick_params(axis='y', which='major', labelsize=fontsizex,pad=1)

	#Set layers

	ax2 = ax.twinx()            
	ax2.set_yticks(y_layers, minor=True)
	ax2.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.6)
	ax2.set_yticks(y_layers_ticks_labes_position, minor=False)
	ax2.set_yticklabels(y_layers_ticks_labes,fontsize=fontsizex)
	ax2.tick_params(axis='y',which='both',length=0)
	ax2.set_ylabel('Layer',fontsize = fontsizey_layers)
	ax2.yaxis.set_label_coords(1.08,0.5)
	ax2.set_ylim(ax.get_ylim())
	plt.tight_layout()

	plt.show()

	fig.savefig('../report/images/vertical_distribution.svg', format='svg') 

def permeability_plot(type_dis,slr,sgr):

	if type_dis=='corey':

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
		ax3=fig.add_subplot(111)
		ax3.plot(saturation,krl,'--k',label='Liquid')
		ax3.plot(saturation,krg,'-k',label='Vapor')
		ax3.set_xlabel("Water saturation",fontsize=26)
		ax3.set_ylabel('Relative permeabilty',fontsize=26)
		ax3.set_ylim([0,1])
		ax3.set_xlim([0,1])
		ax3.legend(loc='lower left',frameon=False,fontsize=26)
		ax3.tick_params(axis='both', which='major', labelsize=26,pad=1)
		yticks = ax3.yaxis.get_major_ticks() 
		yticks[0].label1.set_visible(False)
		plt.show()

		fig.savefig('../report/images/coreys_permeabilities.svg', format='svg') 

def patmfromelev(elev):
	p_atm=(101325*((288+(-0.0065*elev))/288)**(-9.8/(-0.0065*287)))/100000
	return p_atm