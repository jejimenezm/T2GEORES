from T2GEORES import geometry as geomtr
from T2GEORES import formats as formats
import numpy as np
from iapws import IAPWS97
import pandas as pd
import os
from scipy import interpolate
import sys
import json
import math
import matplotlib.pyplot as plt

import seaborn as sns
import pylab as plb
import shapefile
from scipy.interpolate import griddata, interp1d
from scipy.stats import linregress

def patmfromelev(elev):
	"""It fines the atmospheric pressure base on an approximate formula
	
	Parameters
	----------
	elev
	  masl where the pressure is needed

	Returns
	-------
	float
	  Atmospheric pressure in bar

	Examples
	--------
	>>> patmfromelev(750)
	"""

	p_atm=(101325*((288+(-0.0065*elev))/288)**(-9.8/(-0.0065*287)))/100000
	return p_atm

def water_level_projection(MD,P,Tmin):
	"""It projects the water level based on a pressure log

	Parameters
	----------
	MD : array
	  Measure depth array
	P : array
	  Pressure array
	Tmin : float
	  Minimun temperature allowed

	Returns
	-------
	float
	  D2: water leverl projection
	float
	  Pmin: pressure at water level  

	Examples
	--------
	>>> water_level_projection(MD,P,120)
	"""

	#Creation of array with pressure
	P_array=np.linspace(min(P),max(P),4)
	P0=P_array[1]
	P1=P_array[2]

	#Pressure vs MD function
	MDfunc=interpolate.interp1d(P,MD)
	MD0=MDfunc(P0)
	MD1=MDfunc(P1)

	#water_level_assuming saturation temperature at surface
	delta_MD=MD0-MD1
	delta_P=P0-P1
	m=delta_MD/delta_P
	b=MD0-m*P0

	Pmin=IAPWS97(T=(Tmin+273.15),x=0).P*10

	D2=m*Pmin+b

	return D2,Pmin

def initial_conditions(input_dictionary,m,b,use_boiling=True,use_equation=False):
	"""Generates the tempearture and pressure initial conditions assuming boiling from top to bottom layer

	Parameters
	----------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'. Also it contains the keyword 'INCONS_PARAM' with the specified initial conditions, i.e.:'INCONS_PARAM':{'To':30,'GRADTZ':0.08,'DEPTH_TO_SURF':100,'DELTAZ':20}

	Returns
	-------
	list
	  T: initial list of temperature
	list
	  P: initial list of pressure
	list
	  depth: range of depth coming from layers
	"""

	layers_info=geomtr.vertical_layers(input_dictionary)
	
	depths=np.arange(min(layers_info['bottom']),max(layers_info['top'])-input_dictionary['INCONS_PARAM']['WL_FROM_TOP_LAYER'],input_dictionary['INCONS_PARAM']['DELTAZ'])
	Pi=1 #[bar]
	To=input_dictionary['INCONS_PARAM']['To']
	depth=0
	T=[]
	P=[]
	for cnt, TVD in enumerate(depths[::-1]):
		if cnt==0:
			z_ref=max(layers_info['top'])+input_dictionary['INCONS_PARAM']['DEPTH_TO_SURF']
		depth=z_ref-TVD
		Ti=input_dictionary['INCONS_PARAM']['GRADTZ']*depth+To
		rho=IAPWS97(T=(Ti+273.15),x=0.0).rho

		if use_boiling:
			P_colum=rho*input_dictionary['INCONS_PARAM']['DELTAZ']*formats.formats_t2['PARAMETERS']['GF'][0]
			Pi+=P_colum/1E5
			P.append(Pi)
		elif use_equation:
			Px=(TVD-b)/m
			P.append(Px)
		
		T.append(Ti)

	depth_i=np.linspace(max(depths),input_dictionary['z_ref'],input_dictionary['INCONS_PARAM']['DELTAZ'])[::-1]
	Ti=np.linspace(input_dictionary['INCONS_PARAM']['T_SURF'],min(T),len(depth_i))
	Pi=np.linspace(1,min(P),len(depth_i))

	depths=np.append(depth_i,depths[::-1])
	T=np.append(Ti,T)
	P=np.append(Pi,P)

	return T, P, depths

def incons(input_dictionary,m,b,use_boiling=True,use_equation=False):
	"""It returns the coordinates X,Y and Z at a desired depth.

	Parameters
	----------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'. Also it contains the keyword 'INCONS_PARAM' with the specified initial conditions, i.e.:'INCONS_PARAM':{'To':30,'GRADTZ':0.08,'DEPTH_TO_SURF':100,'DELTAZ':20}
	m : float
		Pressure slope on a TVD vs P plot
	b : float
		Pressure intercept on a TVD vs P plot
	use_equation : bool
		If true the variables m and b will be use to extrapolate the values to the bottom layer
	use_boiling : bool
		If true the boiling conditions will be use for calculating the bottom conditions		

	Returns
	-------
	file
	  INCON : on model/t2/sources

	Attention
	---------
	It requires an updated ELEME.json

	Note
	----
	Boiling conditions are assumed

	Examples
	--------
	>>> incons(input_dictionary)
	"""
	input_file='../mesh/ELEME.json'
	T,P,depth=initial_conditions(input_dictionary,m,b,use_boiling,use_equation)
	Tfunc=interpolate.interp1d(depth,T)
	Pfunc=interpolate.interp1d(depth,P)
	output_file='../model/t2/sources/INCON'
	string=""
	if os.path.isfile(input_file):
		eleme_df = pd.read_json(input_file).T
		for index, row in eleme_df.iterrows():
			zi=row['Z']
			Ti=Tfunc(zi)
			Pi=Pfunc(zi)*1E5
			string+="%5s%35s\n"%(index,' ')
			string+=" %19.13E %19.13E\n"%(Pi,Ti)
		file=open(output_file,'w')
		file.write(string)
		file.close()
	else:
		sys.exit("The file %s or directory do not exist"%input_file)

def empty_model(structure, current_path='../'):
	"""It erases all the file on the  T2GEORES structure except the input and scripts folders

	Parameters
	----------
	structure : dictionary
	  It is an internal structure dictionary defined on formats.py	
	current_path : str
	  It specifies the top folder of the structure, if the function is executed from scripts current_path is '../'

	Attention
	---------
	It will erase all the output data, mesh and images on the model.


	Examples
	--------
	>>> empty_model(current_path='../')
	"""
	if formats.structure!=None and len(formats.structure):
		for direc in structure:
			empty_model(formats.structure[direc], os.path.join(current_path, direc))
	else:
		for file in os.listdir(current_path):
			if not any(x in current_path for x in ['input','scripts']):
				try:
					os.remove(os.path.join(current_path,file))
				except IsADirectoryError:
					continue

def create_structure(structure,current_path):
	"""It creates the necessary structure for T2GEORES to work

	Parameters
	----------
	structure : dictionary
	  It is an internal structure dictionary defined on formats.py	
	current_path : str
	  It specifies the path where the structure will be constructed

	Note
	----
	A good practice is to create a folder for the whole model

	Examples
	--------
	>>> create_structure(current_path='.')
	"""
	if structure!=None and len(structure):
		for direc in structure:
			create_structure(structure[direc], os.path.join(current_path, direc))
	else:
		os.makedirs(current_path)

def top_layer_incons(input_dictionary,input_mesh_dictionary,cut_off_T=150,cut_off_P=1):
	"""Modifies the incon file base on real data a the top elevation

	Parameters
	----------
	input_dictionary : dictionary
		List the well names, define the INCONS_PARAM and source_txt file.
	input_mesh_dictionary : dictionary
		Specify the polygon border defiding path
	cut_off_T : float
		The heighest value of temperature a the top layer
	cut_off_P : float
		The heighest value of pressure a the top layer 

	Note
	----
	A file called INCON_MOD will be created on t2/sources

	"""

	#If next value true, some plots showing the points where the data is comming from will be plotted
	plot_input_data = True
	plot_points_to_inter = True
	plot_fix_data_points = True
	plot_contour = True

	layers_info=geomtr.vertical_layers(input_dictionary)

	z0=max(layers_info['middle'])

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	eleme_json_file='../mesh/ELEME.json'

	if os.path.isfile(eleme_json_file):
		with open(eleme_json_file) as file:
		  	blocks=json.load(file)
	else:
		sys.exit("The file %s does not exist"%(eleme_json_file))


	wells_corr_json_file='../mesh/well_dict.txt'

	if os.path.isfile(wells_corr_json_file):
		with open(wells_corr_json_file) as file:
		  	wells_json=json.load(file)
	else:
		sys.exit("The file %s does not exist"%(wells_corr_json_file))

	data_T={well:{'T':0,'P':0,'block':'x','extra':[]} for well in wells}

	T0=input_dictionary['INCONS_PARAM']['To']
	P0=input_dictionary['INCONS_PARAM']['Po']

	for well in wells:
		file_name=well+'_MDPT.dat'
		full_file_name=input_dictionary['source_txt']+'PT/'+file_name
		if os.path.isfile(full_file_name):
			well=file_name.split('_')[0]
			data=pd.read_csv(full_file_name,sep=',')
			funcT=interpolate.interp1d(data['MD'],data['T'])
			funcP=interpolate.interp1d(data['MD'],data['P'])

			try:
				if math.isnan(funcT(geomtr.TVD_to_MD(well,z0))) or funcT(geomtr.TVD_to_MD(well,z0))<0:
					if cut_off_T<min(data['T']):
						data_T[well]['T']=cut_off_T
					else:
						data_T[well]['T']=min(data['T'])
				else:
					Tx=funcT(geomtr.TVD_to_MD(well,z0))
					if T0>Tx:
						data_T[well]['T']=T0
					elif cut_off_T<Tx:
						data_T[well]['T']=cut_off_T
					else:
						data_T[well]['T']=Tx

				if math.isnan(funcP(geomtr.TVD_to_MD(well,z0))) or funcP(geomtr.TVD_to_MD(well,z0))<0:
					if cut_off_P<min(data['P']):
						data_T[well]['P']=cut_off_P
					else:
						data_T[well]['P']=min(data['P'])
				else:
					Px=funcP(geomtr.TVD_to_MD(well,z0))
					if P0>Px:
						data_T[well]['P']=P0
					elif cut_off_P<Px:
						data_T[well]['P']=cut_off_P
					else:
						data_T[well]['P']=Px

			except ValueError:
				data_T[well]['T']=cut_off_T
				data_T[well]['P']=cut_off_P
			data_T[well]['block']='A'+wells_json[well][0]

	shape = shapefile.Reader(input_mesh_dictionary['polygon_shape'])

	#first feature of the shapefile
	feature = shape.shapeRecords()[0]
	points = feature.shape.__geo_interface__ 
	polygon=[]
	for n in points:
		for v in points[n]:
			if n=='coordinates':
				polygon.append([v[0],v[1]]) # (GeoJSON format)


	x_real=[]
	y_real=[]
	names=[]
	
	for block in blocks:
		if block[0]=='A':
			x=blocks[block]['X']
			x_real.append(x)
			y=blocks[block]['Y']
			y_real.append(y)
			names.append(block)

	x_inter=[]
	y_inter=[]
	T_real=[]
	P_real=[]
	
	fix_names=[]
	fix_x=[]
	fix_y=[]
	fix_T=[]
	fix_P=[]
	
	for well in data_T:
		xw=blocks[data_T[well]['block']]['X']
		yw=blocks[data_T[well]['block']]['Y']
		for i,x in enumerate(x_real):
			if np.sqrt((xw-x)**2+(yw-y_real[i])**2)<=150 and (x,y_real[i]) not in list(zip(x_inter,y_inter)):
				T_real.append(data_T[well]['T'])
				P_real.append(data_T[well]['P']+0.92)
				y_inter.append(y_real[i])
				x_inter.append(x)

				fix_x.append(x)
				fix_y.append(y_real[i])
				fix_T.append(data_T[well]['T'])
				fix_P.append(data_T[well]['P']+0.92)
				fix_names.append(names[i])

	for i,x in enumerate(x_real):
		if not check_in_out([x,y_real[i]],polygon):
			x_inter.append(x)
			y_inter.append(y_real[i])
			T_real.append(T0)
			P_real.append(P0)

			fix_x.append(x)
			fix_y.append(y_real[i])
			fix_T.append(T0)
			fix_P.append(P0)
			fix_names.append(names[i])

	x_to_inter=[]
	y_to_inter=[]
	blocks_to_inter=[]
	
	for i,x in enumerate(x_real):
		if (x,y_real[i]) not in list(zip(x_inter,y_inter)):
			x_to_inter.append(x)
			y_to_inter.append(y_real[i])
			blocks_to_inter.append(names[i])

	if plot_input_data:
		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		ax.plot(x_inter,y_inter,'og',linestyle='None',ms=2)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.5)
		ax.tick_params(axis='both', which='major', labelsize=10,pad=0.5)
		fig.savefig("../output/initial_conditions/input_points_top_layer.png",dpi=600) 
		plt.show()

	
	if plot_points_to_inter:
		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		ax.plot(x_to_inter,y_to_inter,'ob',linestyle='None',ms=2)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.5)
		ax.tick_params(axis='both', which='major', labelsize=10,pad=0.5)
		fig.savefig("../output/initial_conditions/points_to_interp_top_layer.png",dpi=600) 
		plt.show()


	T_inter=griddata((x_inter,y_inter),T_real,(x_to_inter,y_to_inter),fill_value=T0,method='linear')
	T_inter=np.nan_to_num(T_inter, nan=T0)
	T_inter[T_inter<min(T_real)]=min(T_real)
	
	P_inter=griddata((x_inter,y_inter),P_real,(x_to_inter,y_to_inter),fill_value=P0,method='linear')
	P_inter=np.nan_to_num(P_inter, nan=P0)
	P_inter[P_inter<min(P_real)]=min(P_real)


	data={'blocks':blocks_to_inter+fix_names,
	      'X':np.append(x_to_inter,fix_x),
	      'Y':np.append(y_to_inter,fix_y),
	      'T':np.append(T_inter,fix_T),
	      'P':np.append(P_inter,fix_P)}

	if plot_contour:
		cm_sea_P=sns.color_palette("YlGnBu", as_cmap=True)
		cm_sea_T=sns.color_palette("YlOrRd", as_cmap=True)
		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_title("Temperature distribution, top layer",fontsize=12)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		c=ax.tricontourf(data['X'], data['Y'], data['T'], cmap=cm_sea_T)#,levels=[20,30,40,50,75,100,125,150]
		cbar=fig.colorbar(c,ax=ax)
		cbar.ax.tick_params(labelsize=10)
		cbar.set_label('Temperature [$^\circ$C]',fontsize=11)
		ax.tick_params(axis='both', which='major', labelsize=10,pad=1)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.05)
		fig.savefig("../output/initial_conditions/T_top_layer.png",dpi=600)
		plt.show()

		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_title("Pressure distribution  top layer",fontsize=12)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		pc=ax.tricontourf(data['X'], data['Y'], data['P'],cmap=cm_sea_P)
		cbar=fig.colorbar(pc,ax=ax)
		cbar.ax.tick_params(labelsize=10)
		cbar.set_label('Pressure [bar]',fontsize=11)
		ax.tick_params(axis='both', which='major', labelsize=10,pad=1)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.05)
		fig.savefig("../output/initial_conditions/P_top_layer.png",dpi=600) 
		plt.show()

	string=""
	for i,block in enumerate(data['blocks']):
		string+="%s\n "%block+format(data['P'][i]*1E5,'>19.13E')+" "+format(data['T'][i],'>19.13E')+'\n'

	incon_file='../model/t2/sources/INCON'
	with open(incon_file) as f:
		lines = f.read().splitlines()
	incon=string+'\n'.join(lines[(len(data['T']))*2:-1])
	
	incon_file_out='../model/t2/sources/INCON_MOD'
	incon_out=open(incon_file_out,'w')
	incon_out.write(incon)
	incon_out.close()

def bottom_layer_incons(input_dictionary,input_mesh_dictionary,m,b,use_boiling=True,use_equation=False,cut_off_T=150,cut_off_P=1):
	"""Modifies the incon file base on real data a the bottom or last known elevation

	Parameters
	----------
	input_dictionary : dictionary
		List the well names, define the INCONS_PARAM and source_txt file.
	input_mesh_dictionary : dictionary
		Specify the polygon border defiding path
	cut_off_T : float
		The heighest value of temperature a the bottom layer
	cut_off_P : float
		The heighest value of pressure a the bottom layer
	use_equation : bool
		If true the variables m and b will be use to extrapolate the values to the bottom layer
	use_boiling : bool
		If true the boiling conditions will be use for calculating the bottom conditions

	Note
	----
	A file called INCON_MOD will be modified on t2/sources.Thus, it has to be used after top_layer_incons
	"""

	T, P, depths =initial_conditions(input_dictionary,m,b,use_boiling,use_equation)

	plot_input_data=True
	plot_points_to_inter=True
	plot_fix_data_points=True
	plot_contour=True

	layers_info=geomtr.vertical_layers(input_dictionary)

	z_l=min(layers_info['middle'])

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	eleme_json_file='../mesh/ELEME.json'

	if os.path.isfile(eleme_json_file):
		with open(eleme_json_file) as file:
		  	blocks=json.load(file)
	else:
		sys.exit("The file %s does not exist"%(eleme_json_file))


	wells_corr_json_file='../mesh/well_dict.txt'

	if os.path.isfile(wells_corr_json_file):
		with open(wells_corr_json_file) as file:
		  	wells_json=json.load(file)
	else:
		sys.exit("The file %s does not exist"%(wells_corr_json_file))

	data_T={well:{'T':0,'P':0,'block':'x','extra':[]} for well in wells}

	T0=input_dictionary['INCONS_PARAM']['To']
	P0=input_dictionary['INCONS_PARAM']['Po']


	src='../input/PT'
	src_files = os.listdir(src)
	slopes=[]
	intercepts=[]
	for well in wells:
		file_name=well+'_MDPT.dat'
		full_file_name=src+'/'+file_name
		if os.path.isfile(full_file_name):
			well=file_name.split('_')[0]
			data=pd.read_csv(full_file_name,sep=',')
			data['TVD']=data.apply(lambda x: geomtr.MD_to_TVD(well,x['MD'])[2],axis=1)

			try:
				slope, intercept, r, p, se = linregress(data[data.P > 30]['P'].tolist(), data[data.P > 30]['TVD'].tolist())
				if slope>-15:
					data_T[well]['P']=(z_l-intercept)/(slope)
				else:
					data_T[well]['P']=P[-1]
			except ValueError:
				data_T[well]['P']=P[-1]

			data_T[well]['T']=data['T'].tail(1).values[0]
			data_T[well]['block']=layers_info['name'][-1]+wells_json[well][0]

	shape = shapefile.Reader(input_mesh_dictionary['polygon_shape'])

	#first feature of the shapefile
	feature = shape.shapeRecords()[0]
	points = feature.shape.__geo_interface__ 
	polygon=[]
	for n in points:
		for v in points[n]:
			if n=='coordinates':
				polygon.append([v[0],v[1]]) # (GeoJSON format)

	x_real=[]
	y_real=[]
	names=[]
	
	for block in blocks:
		if block[0]==layers_info['name'][-1]:
			x=blocks[block]['X']
			x_real.append(x)
			y=blocks[block]['Y']
			y_real.append(y)
			names.append(block)

	x_inter=[]
	y_inter=[]
	T_real=[]
	P_real=[]
	
	fix_names=[]
	fix_x=[]
	fix_y=[]
	fix_T=[]
	fix_P=[]
	
	for well in data_T:
		xw=blocks[data_T[well]['block']]['X']
		yw=blocks[data_T[well]['block']]['Y']
		for i,x in enumerate(x_real):
			if np.sqrt((xw-x)**2+(yw-y_real[i])**2)<=150 and (x,y_real[i]) not in list(zip(x_inter,y_inter)):
				T_real.append(data_T[well]['T'])
				P_real.append(data_T[well]['P']+0.92)
				y_inter.append(y_real[i])
				x_inter.append(x)

				fix_x.append(x)
				fix_y.append(y_real[i])
				fix_T.append(data_T[well]['T'])
				fix_P.append(data_T[well]['P']+0.92)
				fix_names.append(names[i])

	fix_dict={'HEAT_SOURCE':{'X':552612,'Y':263398,'R':750,'T':305,'P':P[-1]}}

	for ID in fix_dict:
		xw=fix_dict[ID]['X']
		yw=fix_dict[ID]['Y']
		for i,x in enumerate(x_real):
			if np.sqrt((xw-x)**2+(yw-y_real[i])**2)<=fix_dict[ID]['R'] and (x,y_real[i]) not in list(zip(x_inter,y_inter)) and check_in_out([x,y_real[i]],polygon):
				T_real.append(fix_dict[ID]['T'])
				P_real.append(fix_dict[ID]['P'])
				y_inter.append(y_real[i])
				x_inter.append(x)

				fix_x.append(x)
				fix_y.append(y_real[i])
				fix_T.append(fix_dict[ID]['T'])
				fix_P.append(fix_dict[ID]['P'])
				fix_names.append(names[i])

	for i,x in enumerate(x_real):
		if not check_in_out([x,y_real[i]],polygon):
			x_inter.append(x)
			y_inter.append(y_real[i])
			T_real.append(T[-1])
			P_real.append(P[-1])

			fix_x.append(x)
			fix_y.append(y_real[i])
			fix_T.append(T[-1])
			fix_P.append(P[-1])
			fix_names.append(names[i])

	x_to_inter=[]
	y_to_inter=[]
	blocks_to_inter=[]
	
	for i,x in enumerate(x_real):
		if (x,y_real[i]) not in list(zip(x_inter,y_inter)):
			x_to_inter.append(x)
			y_to_inter.append(y_real[i])
			blocks_to_inter.append(names[i])

	if plot_input_data:
		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		ax.plot(x_inter,y_inter,'og',linestyle='None',ms=2)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.5)
		ax.tick_params(axis='both', which='major', labelsize=10,pad=1)
		fig.savefig("../output/initial_conditions/input_points_bottom_layer.png") 
		plt.show()

	
	if plot_points_to_inter:
		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		ax.plot(x_to_inter,y_to_inter,'ob',linestyle='None',ms=2)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.5)
		ax.tick_params(axis='both', which='major', labelsize=10,pad=1)
		fig.savefig("../output/initial_conditions/points_to_interp_bottom_layer.png") 
		plt.show()


	T_inter=griddata((x_inter,y_inter),T_real,(x_to_inter,y_to_inter),fill_value=T0,method='linear')
	T_inter=np.nan_to_num(T_inter, nan=T0)
	T_inter[T_inter<min(T_real)]=min(T_real)
	
	P_inter=griddata((x_inter,y_inter),P_real,(x_to_inter,y_to_inter),fill_value=P0,method='linear')
	P_inter=np.nan_to_num(P_inter, nan=P0)
	P_inter[P_inter<min(P_real)]=min(P_real)


	data={'blocks':blocks_to_inter+fix_names,
	      'X':np.append(x_to_inter,fix_x),
	      'Y':np.append(y_to_inter,fix_y),
	      'T':np.append(T_inter,fix_T),
	      'P':np.append(P_inter,fix_P)}

	if plot_contour:
		cm_sea_P=sns.color_palette("YlGnBu", as_cmap=True)
		cm_sea_T=sns.color_palette("YlOrRd", as_cmap=True)
		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_title("Temperature distribution, bottom layer",fontsize=12)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		c=ax.tricontourf(data['X'], data['Y'], data['T'],cmap=cm_sea_T)#,levels=[20,30,40,50,75,100,125,150]
		cbar=fig.colorbar(c,ax=ax)
		cbar.ax.tick_params(labelsize=11)
		cbar.set_label('Temperature [$^\circ$C]',fontsize=11)
		ax.tick_params(axis='both', which='major', labelsize=11,pad=1)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.05)
		fig.savefig("../output/initial_conditions/T_bottom_layer.png")
		plt.show()

		fig= plt.figure(figsize=(12, 12), dpi=300)
		ax=fig.add_subplot(111)
		ax.set_title("Pressure distribution, bottom layer",fontsize=12)
		ax.set_xlabel('East [m]')
		ax.set_ylabel('North [m]')
		ax.set_aspect('equal')
		pc=ax.tricontourf(data['X'], data['Y'], data['P'],cmap=cm_sea_P)
		cbar=fig.colorbar(pc,ax=ax)
		cbar.ax.tick_params(labelsize=11)
		cbar.set_label('Pressure [bar]',fontsize=11)
		ax.tick_params(axis='both', which='major', labelsize=11,pad=1)
		ax.plot(x_real,y_real,'ok',linestyle='None',ms=0.05)
		fig.savefig("../output/initial_conditions/P_bottom_layer.png") 
		plt.show()


	string=""
	for i,block in enumerate(data['blocks']):
		string+="%s\n "%block+format(data['P'][i]*1E5,'>19.13E')+" "+format(data['T'][i],'>19.13E')+'\n'
	

	incon_file='../model/t2/sources/INCON_MOD'
	with open(incon_file) as f:
		lines = f.read().splitlines()
	incon='\n'.join(lines[0:(-len(data['T']))*2	])+'\n'+string

	incon_file_out='../model/t2/sources/INCON_MOD'
	incon_out=open(incon_file_out,'w')
	incon_out.write(incon)
	incon_out.close()

def incon_to_steinar(sav = None):
	"""It converts the modified INCON file (INCON_MOD) to steinar input

	Note
	----
	It will write a file called incon_to_steinar on the sources file

	Examples
	--------
	>>> create_structure(current_path='.')
	"""


	if sav == None:
		incon_file='../model/t2/sources/INCON_MOD'
	elif sav == 'init':
		incon_file = '../model/t2/INCON'
	elif sav == 't2.sav':
		incon_file='../model/t2/t2.sav'
	elif sav == 'SAVE1':
		incon_file='../model/t2/SAVE1'

	string=""
	with open(incon_file) as file:
	    for i, line in enumerate(file):
	    	if i!=0:
	    		try:
			    	if line[0].isalpha():
			    		string+=line[0:5]+'    0    0         0.0000\n'
			    	else:
			    		string+=format(float(line[1:20]),'>20.13E')+format(float(line[20:40]),'>20.13E')+'\n'
	    		except ValueError:
	    			break
	    			
	incon_steinar='../mesh/to_steinar/incon_to_steinar'
	file=open(incon_steinar,'w')
	file.write(string)
	file.close()

def check_in_out(point,borders):
	"""It checks if a point is outside or inside of a given area

	Parameters
	----------
	point : array
		x and y position
	borders : array
		Contains the array defining a close polygon
	"""


	polygon=borders
	boolean=False
	cnt=0
	for n in range(len(polygon)):
		if n+1!=len(polygon):
			m,b=plb.polyfit([polygon[n][0],polygon[n+1][0]],[polygon[n][1],polygon[n+1][1]],1)
			val_range=[polygon[n][1],polygon[n+1][1]]
		elif n+1==len(polygon):
			m,b=plb.polyfit([polygon[-1][0],polygon[0][0]],[polygon[-1][1],polygon[0][1]],1)
			val_range=[polygon[-1][1],polygon[0][1]]
		
		x=(point[1]-b)/m
		if point[0]<x and min(val_range)<point[1] and point[1]<max(val_range):
			cnt+=1
	if cnt==1:
		boolean=True

	return boolean



def incon_from_steinar():

	incon_file = '../mesh/to_steinar/incon'

	string=""
	with open(incon_file) as file:
	    for i, line in enumerate(file):
    		try:
		    	if line[0].isalpha():
		    		string+=line[0:5]+'\n'
		    	else:
		    		string+=format(float(line[0:20]),'>20.13E')+format(float(line[20:40]),'>20.13E')+'\n'
    		except ValueError:
    			break
	    			
	incon_steinar='../model/t2/sources/STE_INCON'
	file=open(incon_steinar,'w')
	file.write(string)
	file.close()