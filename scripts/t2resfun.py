#from model_conf import *
import numpy as np
import pyamesh as pya
import shutil
import os
import matplotlib.pyplot as plt
import csv
from scipy import interpolate
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import os
import sys
from model_conf import *
import sqlite3


def vertical_layer(layers,z0_level):

	"""Return:
	   Top masl of every layer
	   Namer of every the layer
	   Middle masl of every layer
	"""

	y_layers_top=[]
	y_layers_bottom=[]
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
		y_layers_top.append(z_top)
		y_layers_bottom.append(z_bottom)

		layers[keys].extend((z_top,z_bottom))
		y_layers_ticks_labes.append(layers[keys][0])
		y_layers_ticks_labes_position.append((z_top+z_bottom)*0.5)

	return y_layers_top,y_layers_ticks_labes, y_layers_ticks_labes_position,y_layers_bottom

def mesh_creation_func(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers,layer_to_plot,x_space,y_space,radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,plot_names,plot_centers,z0_level,\
			mesh_creation,plot_layer,to_steinar,to_GIS,plot_all_GIS,from_leapfrog):
	
	layers_thick=map(float,np.array(layers.values())[:][:,1])

	blocks=pya.py2amesh(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers_thick,layer_to_plot,x_space,y_space,radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,plot_names,plot_centers,z0_level,plot_all_GIS,from_leapfrog)
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

	y_layers,y_layers_ticks_labes, y_layers_ticks_labes_position,y_layers_bottom=vertical_layer(layers,z0_level)

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

def MD_to_TVD_one_var_array(well,var_array,MD_array,num_points):
	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')

	reader = csv.DictReader(open('../input/ubication.csv', 'rb'))
	dict_ubication={}
	for line in reader:
		dict_ubication[line['well']]=line
	z_0=float(dict_ubication[well]['elevation'])
	x_0=float(dict_ubication[well]['east'])
	y_0=float(dict_ubication[well]['north'])

	#Initialize the delta z values
	z_delta=[0 for i in MD]
	x=[0 for i in MD]
	y=[0 for i in MD]
	z=[0 for i in MD]

	#Assuming straight line between points
	for j in range(len(MD)):
		if j==0:
			z_delta[j]=0
		else:
			z_delta[j]=((MD[j]-MD[j-1])**2-(DeltaX[j]-DeltaX[j-1])**2-(DeltaY[j]-DeltaY[j-1])**2)**0.5+z_delta[j-1]
	
	#Convertion delta to absolute
	for j in range(len(MD)):
		x[j]=x_0+DeltaX[j]
		y[j]=y_0+DeltaY[j]
		z[j]=z_0-z_delta[j]

	#Function of X-Y-Z with MD
	funxmd=interpolate.interp1d(MD,x)
	funymd=interpolate.interp1d(MD,y)
	funzmd=interpolate.interp1d(MD,z)

	#Working with variable

	funcV=interpolate.interp1d(MD_array,var_array)
	x_V=[]
	y_V=[]
	z_V=[]
	var_V=[]

	MD_array_reconvert=np.linspace(min(MD_array),max(MD_array),num_points)

	for i in MD_array_reconvert:
		try:
			x_V.append(funxmd(i))
			y_V.append(funymd(i))
			z_V.append(funzmd(i))
			var_V.append(funcV(i))
		except ValueError:
			pass

	return x_V,y_V,z_V,var_V

def MD_to_TVD(well,depth):
	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')

	reader = csv.DictReader(open('../input/ubication.csv', 'rb'))
	dict_ubication={}
	for line in reader:
		dict_ubication[line['well']]=line
	z_0=float(dict_ubication[well]['elevation'])
	x_0=float(dict_ubication[well]['east'])
	y_0=float(dict_ubication[well]['north'])

	#Initialize the delta z values
	z_delta=[0 for i in MD]
	x=[0 for i in MD]
	y=[0 for i in MD]
	z=[0 for i in MD]

	#Assuming straight line between points
	for j in range(len(MD)):
		if j==0:
			z_delta[j]=0
		else:
			z_delta[j]=((MD[j]-MD[j-1])**2-(DeltaX[j]-DeltaX[j-1])**2-(DeltaY[j]-DeltaY[j-1])**2)**0.5+z_delta[j-1]
	
	#Convertion delta to absolute
	for j in range(len(MD)):
		x[j]=x_0+DeltaX[j]
		y[j]=y_0+DeltaY[j]
		z[j]=z_0-z_delta[j]

	#Function of X-Y-Z with MD
	funxmd=interpolate.interp1d(MD,x)
	funymd=interpolate.interp1d(MD,y)
	funzmd=interpolate.interp1d(MD,z)

	try:
		x=funxmd(depth)
		y=funymd(depth)
		z=funzmd(depth)
	except ValueError:
		pass
	return x,y,z

def plot_one_drawdown_from_txt(well,depth):

	#Read file
	file="../input/drawdown/%s_DD.dat"%well
	data=pd.read_csv("../input/drawdown/%s_DD.dat"%well)
	data.loc[data['TVD']==depth]['datetime']
	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
	dates=list(map(dates_func,data.loc[data['TVD']==depth]['datetime'].values))

	#Plotting

	fig, ax = plt.subplots(figsize=(10,4))
	ax.plot(dates,data.loc[data['TVD']==depth]['pressure'].values,'ob',linewidth=1,ms=3,label='drawdown')
	ax.set_title("Well: %s at %s masl"%(well,depth) ,fontsize=8)
	ax.set_xlabel("Time",fontsize = 8)
	ax.set_ylabel('Pressure [bar]',fontsize = 8)


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
	
	return plt.show()

def plot_one_cooling_from_txt(well,depth):

	#Read file
	file="../input/drawdown/%s_C.dat"%well
	data=pd.read_csv("../input/cooling/%s_C.dat"%well)
	data.loc[data['TVD']==depth]['datetime']
	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
	dates=list(map(dates_func,data.loc[data['TVD']==depth]['datetime'].values))

	#Plotting

	fig, ax = plt.subplots(figsize=(10,4))
	ax.plot(dates,data.loc[data['TVD']==depth]['temperature'].values,'or',linewidth=1,ms=3,label='cooling')
	ax.set_title("Well: %s at %s masl"%(well,depth) ,fontsize=8)
	ax.set_xlabel("Time",fontsize = 8)
	ax.set_ylabel('Temperature [C]',fontsize = 8)

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
	
	return plt.show()

def plot_one_cooling_and_drawdown_from_txt(well,depth):

	dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")

	#Read file cooling
	data_c=pd.read_csv("../input/cooling/%s_C.dat"%well)
	dates_c=list(map(dates_func,data_c.loc[data_c['TVD']==depth]['datetime'].values))

	#Read file DRAWDOWN
	data_d=pd.read_csv("../input/drawdown/%s_DD.dat"%well)
	dates_d=list(map(dates_func,data_d.loc[data_d['TVD']==depth]['datetime'].values))
	if len(dates_d)==0:
		print "There is not values for this depth"
	else:
		#Plotting

		fig, ax = plt.subplots(figsize=(10,4))
		ax2 = ax.twinx()

		#Plotting drawdown
		ax.plot(dates_d,data_d.loc[data_d['TVD']==depth]['pressure'].values,'ob',linewidth=1,ms=3,label='drawdown',alpha=0.75)
		ax.set_title("Well: %s at %s masl"%(well,depth) ,fontsize=8)
		ax.set_xlabel("Time",fontsize = 8)
		ax.set_ylabel('Pressure [bar]',fontsize = 8)

		#Plotting cooling
		ax2.plot(dates_c,data_c.loc[data_c['TVD']==depth]['temperature'].values,'or',linewidth=1,ms=3,label='cooling',alpha=0.75)
		ax2.set_ylabel('Temperature [C]',fontsize = 8)


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

	dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")

	#Read file cooling
	data=pd.read_csv('../input/mh/%s_mh.dat'%well)
	dates=list(map(dates_func,data['date-time'].values))

	gs = gridspec.GridSpec(3, 1)

	fig, ax = plt.subplots(figsize=(10,4))
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

	ax=plt.subplot(gs[0,0])
	ln1=ax.plot(dates,data['steam'],'-or',linewidth=1,ms=1,label='Steam',alpha=0.75)

	ax1b = ax.twinx()
	ln2=ax1b.plot(dates,data['liquid'],'-ob',linewidth=1,ms=1,label='Liquid',alpha=0.75)
	ax.set_ylabel('Flow [kg/s]',fontsize = 8)
	
	# added these three lines
	lns = ln1+ln2
	labs = [l.get_label() for l in lns]
	ax.legend(lns, labs, loc="upper right")

	ax2=plt.subplot(gs[1,0])
	ax2.plot(dates,data['enthalpy'],'-ok',linewidth=1,ms=1,label='Enthalpy',alpha=0.75)
	ax2.legend(loc="upper right")
	ax2.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)

	ax3=plt.subplot(gs[2,0])
	ax3.plot(dates,data['WHPabs'],'-og',linewidth=1,ms=1,label='Pressure',alpha=0.75)
	ax3.legend(loc="upper right")
	ax3.set_ylabel('Pressure [bara]',fontsize = 8)

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	plt.setp(ax.get_xticklabels(), visible=False)
	plt.setp(ax2.get_xticklabels(), visible=False)

	ax.xaxis.set_major_formatter(years_fmt)
	ax2.xaxis.set_major_formatter(years_fmt)
	ax3.xaxis.set_major_formatter(years_fmt)

	plt.show()

def conne_from_steinar_to_t2():
	file_source_dir='../mesh/to_steinar'
	file_in='conne'
	file_output_dir='../model/t2/sources'
	file_out='CONNE'

	string="CONNE----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	if os.path.isfile(file_source_dir+'/'+file_in):
		with open(file_source_dir+'/'+file_in) as rock_file:
			for line in rock_file.readlines()[1:]:
				linex=line.split()
				if float(linex[8])<=0:
					string+="%10s%20s%10.3E%10.3E%10.3E%10.2f\n"%(linex[0],int(linex[4]),float(linex[5]),float(linex[6]),float(linex[7]),float(linex[8]))
				else:
					string+="%10s%20s%10.3E%10.3E%10.3E%10.2f\n"%(linex[0],int(linex[4]),float(linex[5]),float(linex[6]),float(linex[7]),-1*float(linex[8]))
		file=open(file_output_dir+'/'+file_out,'w')
		file.write(string)
		file.close()
	else:
		print "The file or directory do not exist"
	#A110AA127    0    0    0   1 9.418E+01 9.418E+01 1.956E+04      0.0 0.0000E+00

def merge_eleme_and_in_to_t2():
	in_file="../mesh/to_steinar/in"
	eleme_file="../mesh/to_steinar/eleme"

	if os.path.isfile(in_file) and os.path.isfile(eleme_file):
		string="ELEME----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
		data_in=pd.read_csv(in_file,delim_whitespace=True,skiprows=7,header=None,names=['block','li','X','Y','Z','h'])
		data_eleme=pd.read_csv(eleme_file,delim_whitespace=True,skiprows=1,header=None,names=['block','rocktype','vol'])
		data_in.set_index('block')
		data_eleme.set_index('block')

		for n in range(len(data_eleme['block'])):
			selection=data_in.loc[data_in['block']==data_eleme['block'][n]].values.tolist()
			if data_eleme['vol'][n]>-1E100:
				string+="%5s%10s%5s%10.3E%10s%10.3E%10.3E%10.3E\n"%(data_eleme['block'][n],\
	                                                                      " ",\
	                                                data_eleme['rocktype'][n],\
	                                                     data_eleme['vol'][n],\
	                                                                       " ",\
	                                                           selection[0][2],\
	                                                           selection[0][3],\
	                                                           selection[0][4])

			else:
				string+="%5s%10s%5s%10s%10s%10.3E%10.3E%10.3E\n"%(data_eleme['block'][n],\
					                                                                      " ",\
					                                                data_eleme['rocktype'][n],\
					                                                                       " ",\
					                                                                       " ",\
					                                                           selection[0][2],\
					                                                           selection[0][3],\
					                                                           selection[0][4])

		file=open('../model/t2/sources/ELEME','w')
		file.write(string)
		file.close()

def t2_input_creation(param,multi,solver,recap,type_run,title):

	string="*%s\n"%(title)

	if os.path.isfile('../mesh/to_steinar/rocks'):
		#Writing ROCK SECTION
		string+="ROCKS----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
		with open('../mesh/to_steinar/rocks') as rock_file:
			for line in rock_file.readlines()[:]:
				string+="%s\n"%line[0:80]
		string+="\n"
	else:
		sys.exit("Error message: the rock file on ../mesh/to_steinar/rocks is not prepared")

	#Writing PARAM SECTION

	string+="""START----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8
----*----1 MOP: 123456789*123456789*1234 ---*----5----*----6----*----7----*----8
PARAM----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""

	skip=False

	for dictionary in param:
		for index, key in enumerate(dictionary):
			if len(dictionary[key])==3:
				skip=False
				if dictionary[key][1]!=None and 's' in dictionary[key][2]:
					string+=format(str(dictionary[key][1]),"%s"%dictionary[key][2])
				elif 's' not in dictionary[key][2] and dictionary[key][1]!=None:
					string+=format(dictionary[key][1],"%s"%dictionary[key][2])
				elif dictionary[key][1]==None and 'E' not in dictionary[key][2]:
					string+=format("","%s"%dictionary[key][2])
				elif dictionary[key][1]==None and 'E' in dictionary[key][2]:
					string+=format("",">%ss"%dictionary[key][2].split('.')[0].split('>')[1])
			if len(dictionary[key])==2:
				skip=False
				string+=format(dictionary[key][0],"%s"%dictionary[key][1])
				if key%8==0:
					string+="\n"
				if key>100:
					break
			if len(dictionary)==1:
				skip=True
		if not skip: #Every time a dictionary finish
			string+="\n"

	string+="\n"

	#Writing MULTI SECTION

	string+="""MULTI----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""

	for index, key in enumerate(multi):
		if len(multi[key])==3:
			skip=False
			if multi[key][1]!=None and 's' in multi[key][2]:
				string+=format(str(multi[key][1]),"%s"%multi[key][2])
			elif 's' not in multi[key][2] and multi[key][1]!=None:
				string+=format(multi[key][1],"%s"%multi[key][2])
			elif multi[key][1]==None and 'E' not in multi[key][2]:
				string+=format("","%s"%multi[key][2])
			elif multi[key][1]==None and 'E' in multi[key][2]:
				string+=format("",">%ss"%multi[key][2].split('.')[0].split('>')[1])
	string+="\n\n"

	#Writing SOLVR SECTION

	string+="""SOLVR----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""

	for index, key in enumerate(solver):
		if len(solver[key])==3:
			skip=False
			if solver[key][1]!=None and 's' in solver[key][2]:
				string+=format(str(solver[key][1]),"%s"%solver[key][2])
			elif 's' not in solver[key][2] and solver[key][1]!=None:
				string+=format(solver[key][1],"%s"%solver[key][2])
			elif solver[key][1]==None and 'E' not in solver[key][2]:
				string+=format("","%s"%solver[key][2])
			elif solver[key][1]==None and 'E' in solver[key][2]:
				string+=format("",">%ss"%solver[key][2].split('.')[0].split('>')[1])
	string+="\n\n"

	#Writing RPCAP SECTION

	string+="""RPCAP----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""

	for index, key in enumerate(recap):
		if len(recap[key])==3:
			skip=False
			if recap[key][1]!=None and 's' in recap[key][2]:
				string+=format(str(recap[key][1]),"%s"%recap[key][2])
			elif 's' not in recap[key][2] and recap[key][1]!=None:
				string+=format(recap[key][1],"%s"%recap[key][2])
			elif recap[key][1]==None and 'E' not in recap[key][2]:
				string+=format("","%s"%recap[key][2])
			elif recap[key][1]==None and 'E' in recap[key][2]:
				string+=format("",">%ss"%recap[key][2].split('.')[0].split('>')[1])
		if key%9==0:
			string+="\n"
	string+="\n"


	string+="""FOFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
	if os.path.isfile('../model/t2/sources/FOFT'):
		with open('../model/t2/sources/FOFT') as rock_file:
			for line in rock_file.readlines()[:]:
				string+="%s"%line
		string+="\n"
	else:
		sys.exit("Error message: the FOFT file on ../model/t2/FOFT is not prepared, run write_wells_track_blocks_from_sqlite_to_FOFT or write_well_sources_from_sqlite_to_FOFT")

	#Writing PARAM SECTION

	string+="""TIMES----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""

	skip=False

	for dictionary in times:
		for index, key in enumerate(dictionary):
			if len(dictionary[key])==3:
				skip=False
				if dictionary[key][1]!=None and 's' in dictionary[key][2]:
					string+=format(str(dictionary[key][1]),"%s"%dictionary[key][2])
				elif 's' not in dictionary[key][2] and dictionary[key][1]!=None:
					string+=format(dictionary[key][1],"%s"%dictionary[key][2])
				elif dictionary[key][1]==None and 'E' not in dictionary[key][2]:
					string+=format("","%s"%dictionary[key][2])
				elif dictionary[key][1]==None and 'E' in dictionary[key][2]:
					string+=format("",">%ss"%dictionary[key][2].split('.')[0].split('>')[1])
				if key%8==0:
					string+="\n"
				if key>100:
					break
			if len(dictionary)==1:
				skip=True

		if not skip: #Every time a dictionary finish
			string+="\n"

	string+="\n"



	if os.path.isfile('../model/t2/sources/ELEME'):
		merge_eleme_and_in_to_t2()
		with open('../model/t2/sources/ELEME') as rock_file:
			for line in rock_file.readlines()[:]:
				string+="%s"%line
		string+="\n"
	else:
		sys.exit("Error message: the ELEME file on ../model/t2/sources/ELEME is not prepared")


	if os.path.isfile('../model/t2/sources/CONNE'):
		conne_from_steinar_to_t2()
		with open('../model/t2/sources/CONNE') as conne_file:
			for line in conne_file.readlines()[:]:
				string+="%s"%line
		string+="\n"
	else:
		sys.exit("Error message: the CONNE file on ../model/t2/sources/CONNE is not prepared")


	string+="GENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	if os.path.isfile('../model/t2/sources/GENER_SOURCES'):
		with open('../model/t2/sources/GENER_SOURCES') as gener_source_file:
			for line in gener_source_file.readlines()[:]:
				string+="%s"%line
		if type_run!='production':
			string+="\n"
	else:
		sys.exit("""Error message: the GENER_SOURCES file on ../model/t2/sources/GENER_SOURCES is not prepared\n
			        you might want to run write_geners_to_txt_and_sqlite on t2gener.py file""")

	if type_run=='production':
		if os.path.isfile('../model/t2/sources/GENER_PROD'):
			with open('../model/t2/sources/GENER_PROD') as gener_prod_file:
				for line in gener_prod_file.readlines()[:]:
					string+="%s"%line
			string+="\n"
		else:
			sys.exit("""Error message: the GENER_PROD file on ../model/t2/sources/GENER_PROD is not prepared\n
				        you might want to run write_gener_from_sqlite on t2gener.py file""")

	string+="ENDCY----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	string+="\n"

	file=open('../model/t2/t2','w')
	file.write(string)
	file.close()

def write_wells_track_blocks_from_sqlite_to_FOFT(db_path):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY middle;",conn)

	string=""
	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in sorted(data_layer['correlative'].values):
				string+="%s\n"%(n+data_block['blockcorr'].values[0])
	conn.close()
	file=open('../model/t2/sources/FOFT','w')
	file.write(string)
	file.close()


def write_well_sources_from_sqlite_to_FOFT(db_path):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_blockcorr=pd.read_sql_query("SELECT blockcorr FROM t2wellsource WHERE source_nickname LIKE 'SRC%';",conn)

	string=""
	for n in sorted(data_blockcorr['blockcorr'].values):
		string+="%s\n"%(n)

	conn.close()
	file=open('../model/t2/sources/FOFT','w')
	file.write(string)
	file.close()

db_path='../input/model.db'

"""
mesh_creation_func(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers,layer_to_plot,x_space,y_space,radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,plot_names,plot_centers,z0_level,\
			mesh_creation,plot_layer,to_steinar,to_GIS,plot_all_GIS,from_leapfrog)
"""
#write_gener_from_sqlite(db_path,wells)
#plot_one_mh_from_txt('AH-28')
#plot_one_mh_from_txt('CH-7BIS')
#plot_one_cooling_and_drawdown_from_txt('AH-34',100)

###NATURAL STATE



#FROM txt2sqlite.py
#insert_wellblock_to_sqlite(db_path,source_txt,wells)
#insert_layers_to_sqlite(db_path,source_txt)

#conne_from_steinar_to_t2()
#merge_eleme_and_in_to_t2()
#write_wells_track_blocks_from_sqlite(db_path)
#write_well_sources_from_sqlite_to_FOFT(db_path)

#FROM t2gener.py
#write_gener_from_sqlite(db_path,wells)

#t2_input_creation(param,multi,solver,recap,type_run,title)

#PRODUCTION STATE

#write_geners_to_txt_and_sqlite(db_path,geners)
