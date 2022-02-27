from T2GEORES import formats as formats
import numpy as np
import csv
from scipy import interpolate
import pandas as pd
import sys
import shapefile
import json
from iapws import IAPWS97
import sqlite3
import math


def vertical_layers(input_dictionary):
	"""It returns the layers information on a dictionary

	Returns
	-------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'.

	Returns
	-------
	dictionary
		layers_info: dictionary with keywords; name, top, middle and bottom. The last three are float values
	
	"""

	layers_info={'name':[],'top':[],'middle':[],'bottom':[]}

	depth=0

	layers=input_dictionary['LAYERS']
	for cnt, layer in enumerate(sorted(layers)):
		depth+=layers[layer][1]
		z_bottom=input_dictionary['z_ref']-depth
		if cnt==0:
			z_top=input_dictionary['z_ref']
		else:
			z_top+=-layers[last_key][1]
		last_key=layer

		z_mid=(z_top+z_bottom)*0.5

		layers_info['name'].append(layers[layer][0])
		layers_info['top'].append(z_top)
		layers_info['middle'].append(z_mid)
		layers_info['bottom'].append(z_bottom)

	return layers_info

def MD_to_TVD(well,depth):
	"""It returns the coordinates X,Y and Z at a desired depth.

	Parameters
	----------
	well : str
	  Selected well
	depth : float
	  Measure depth at which the X,Y,Z coordinate is needed

	Returns
	-------
	float
	  x_V :  x position of desire point
	float
	  y_V :  y position of desire point
	float
	  z_V :  z position of desire point
	  
	Attention
	---------
	The input information comes from the files input/ubication.csv and  input/survey/{well}_MD.dat.

	Note
	----
	A linear regression is used.

	Examples
	--------
	>>> MD_to_TVD('WELL-1',500)
	"""

	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')

	reader = csv.DictReader(open("../input/ubication.csv", 'r')) #'rb'
	dict_ubication={}
	for line in reader:
		dict_ubication[line['well']]=line
	z_0=float(dict_ubication[well]['masl'])
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
		x_out=funxmd(depth)
		y_out=funymd(depth)
		z_out=funzmd(depth)
	except ValueError:
		x_out=np.nan
		y_out=np.nan
		z_out=np.nan
	return x_out,y_out,z_out

def MD_to_TVD_one_var_array(well,var_array,MD_array):
	"""It returns the position X, Y and Z for every point on a log along Pressure or Temperature.

	Parameters
	----------
	well : str
	  Selected well
	var_array : array
	  It contains the log of pressure or temperature
	MD_array :array
	  It contains the measure depth values corresponding with every point on var_array

	Returns
	-------
	float
	  x_V :  x position of desire point
	float
	  y_V :  y position of desire point
	float
	  z_V :  z position of desire point
	array
	  v_V : contains the values of pressure or temperature for every coordinate
	  
	Attention
	---------
	The input information comes from the files input/ubication.csv and  input/survey/{well}_MD.dat.

	Note
	----
	A linear regression is used.

	Examples
	--------
	>>> MD_to_TVD_one_var_array('WELL-1',data['Temp'],data['MD'],100)
	"""

	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')

	reader = csv.DictReader(open("../input/ubication.csv", 'r'))
	dict_ubication={}
	for line in reader:
		dict_ubication[line['well']]=line
	z_0=float(dict_ubication[well]['masl'])
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

	#MD_array_reconvert=np.linspace(min(MD_array),max(MD_array),num_points)

	for value in MD_array:
		try:
			x_V.append(funxmd(value))
			y_V.append(funymd(value))
			z_V.append(funzmd(value))
			var_V.append(funcV(value))
		except ValueError:
			pass

	return x_V,y_V,z_V,var_V

def TVD_to_MD(well,TVD):
	"""It returns the measure depth position for a well based on a true vertical depth

	Parameters
	----------
	well : str
	  Selected well
	TVD : float
	  Desire true vertical depth

	Returns
	-------
	float
	  MD :  measure depth

	Attention
	---------
	The input information comes from the files input/ubication.csv and  input/survey/{well}_MD.dat.

	Note
	----
	A linear regression is used.

	Examples
	--------
	>>> TVD_to_MD('WELL-1',-100)
	"""

	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')

	reader = csv.DictReader(open("../input/ubication.csv", 'r')) #'rb'
	dict_ubication={}
	for line in reader:

		dict_ubication[line['well']]=line
	z_0=float(dict_ubication[well]['masl'])
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
		z[j]=z_0-z_delta[j]

	#Function of X-Y-Z with MD
	funzmd=interpolate.interp1d(z,MD)


	try:
		MD=funzmd(TVD)
	except ValueError:
		MD=np.nan
	return MD

def TVD_to_MD_array(well,TVD_array):
	"""It returns the measure depths for a desire list of true vertical depth values

	Parameters
	----------
	well : str
	  Selected well
	TVD_array : list
	  List of true vertical depth values

	Returns
	-------
	array
	  MD : list of measure depth values
	  
	Attention
	---------
	The input information comes from the files input/ubication.csv and  input/survey/{well}_MD.dat.

	Note
	----
	A linear regression is used.

	Examples
	--------
	>>>TVD_to_MD_array('WELL-1,data['TVD'])
	"""

	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')

	reader = csv.DictReader(open("../input/ubication.csv", 'r')) #'rb'
	dict_ubication={}
	for line in reader:

		dict_ubication[line['well']]=line
	z_0=float(dict_ubication[well]['masl'])
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
		z[j]=z_0-z_delta[j]

	#Function of X-Y-Z with MD
	funzmd=interpolate.interp1d(z,MD)

	MD=[]
	for v in TVD_array:
		try:
			MD.append(funzmd(v))
		except ValueError:
			MD.append(np.nan)
	return MD

def remap(data):
	"""It returns an array with the number of values as the reference pressure array 

	Parameters
	----------
	data : dict
	  Contains 'MD_P','P' and 'MD_T' at least. The depths values for P are found base on the depths of MD_T

	Returns
	-------
	dict
	  data : with 'remap_P' cointaning the values of P for the depths listed at MD_T
	"""

	map_function=interpolate.interp1d(data['MD_P'],data['P'])

	p=[]
	for MD in data['MD_T']:
		try:
			p.append(map_function(MD))
		except ValueError:
			p.append(np.nan)

	data['remap_P']=p

	return data

def line_intersect(Ax1, Ay1, Ax2, Ay2, Bx1, By1, Bx2, By2):
	"""Finds the intersection point between two lines

	Parameters
	----------	  
	{letter}{position}{corr} : float
	  Identifies the point A or B, the position (x or y ) and the correlative (1 or 2)

	Returns
	-------
	tuple
	  (x,y), if there is no intersection, None value is returned
	"""

	d = (By2 - By1) * (Ax2 - Ax1) - (Bx2 - Bx1) * (Ay2 - Ay1)
	if d:
		uA = ((Bx2 - Bx1) * (Ay1 - By1) - (By2 - By1) * (Ax1 - Bx1)) / d
		uB = ((Ax2 - Ax1) * (Ay1 - By1) - (Ay2 - Ay1) * (Ax1 - Bx1)) / d
	else:
		return
	if not(0 <= uA <= 1 and 0 <= uB <= 1):
		return
	x = Ax1 + uA * (Ax2 - Ax1)
	y = Ay1 + uA * (Ay2 - Ay1)

	return x, y

def write_well_track(input_dictionary):
	"""It converts every specified well survey using measure depth on true vertical depth survey

	Parameters
	----------	  
	input_dictionary : dictionary
	   Contains list of wells under the keywords 'WELLS', 'MAKE_UP_WELLS' and 'NOT_PRODUCING_WELL'. It also needs to contain the input files path.

	Returns
	-------
	file
	  {pozo}_xyz.csv: on ../input/survey/xyz

	Examples
	--------
	>>> write_well_track(input_dictionary)
	"""

	source_txt=input_dictionary['source_txt']

	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells.append(well)
		except KeyError:
				pass

	for well in wells:
		try:
			well_survey=pd.read_csv(source_txt+'survey/'+well+"_MD.dat")
			file=open(source_txt+'survey/'+well+"_xyz.csv","w")
			string="x,y,z\n"
			file.write(string)
			for index,row in well_survey.iterrows():
				x,y,z=MD_to_TVD(well,row['MeasuredDepth'])
				string="%s,%s,%s\n"%(x,y,z)
				file.write(string)
			file.close()
		except FileNotFoundError:
			sys.exit("There is no MD file for the well %s"%well)

def write_feedzone_position(input_dictionary):
	""" It generates a file on csv format containing the well feedzone position and coordinates.

	Parameters
	----------	  
	input_dictionary : dictionary
	  Contains the path of the input files under the keyword 'sources_txt'

	Returns
	-------
	file
	  well_feezone_xyz: on ../input

	Note
	----
	regeo_mesh uses this file as an input

	Examples
	--------
	>>> write_feedzone_position(source_txt='../input/')
	"""

	source_txt=input_dictionary['source_txt']

	source_file=source_txt+'well_feedzone.csv'
	try:
		feedzones=pd.read_csv(source_file,delimiter=",")	
	except FileNotFoundError:
		sys.exit("There is no MD file for the well %s"%source_file)

	file=open('../input/well_feedzone_xyz.csv','w')

	string="well,MD,x,y,z,type\n"
	file.write(string)
	for index,row in feedzones.iterrows():
		x,y,z=MD_to_TVD(row['well'],row['MD'])
		string="%s,%s,%s,%s,%s,%s\n"%(row['well'],row['MD'],x,y,z,row['type'])
		print(string)
		file.write(string)
	file.close()

def write_feedzone_position_from_dict(wells):
	""" It generates a file on csv format containing the well feedzone position and coordinates from a python dictionary with well information

	Parameters
	----------	  
	wells : dictionary
	  Contains the wells names, feedzone and contribution

	Returns
	-------
	file
	  well_feedzone_xyz: on ../input

	Note
	----
	regeo_mesh uses this file as an input

	Examples
	--------
	>>> wells={'TR-1':{type_w':'OBS','feedzones':{'A':{'MD':600,'contribution':1}}}},
	>>> write_feedzone_position_from_dict(wells)
	"""

	file=open('../input/'+'well_feedzone_xyz.csv','w')

	string="well,MD,x,y,z,type\n"
	file.write(string)
	for well in wells:
		for i in wells[well]['feedzones']:
			x,y,z=MD_to_TVD(well,wells[well]['feedzones'][i]['MD'])
			string="%s,%s,%s,%s,%s,%s\n"%(well,wells[well]['feedzones'][i]['MD'],x,y,z,wells[well]['type_w'])
			file.write(string)
	file.close()

def write_feedzone_from_dict(wells):
	""" It generates a file on csv format containing the well feedzone position and coordinates from a python dictionary with well information

	Parameters
	----------	  
	wells : dictionary
	  Contains the wells names, feedzone and contribution

	Returns
	-------
	file
	  well_feedzone: on ../input

	Note
	----
	regeo_mesh uses this file as an input

	Examples
	--------
	>>> wells={'TR-1':{type_w':'OBS','feedzones':{'A':{'MD':600,'contribution':1}}}},
	>>> write_feedzone_position_from_dict(wells)
	"""

	file=open('../input/'+'well_feedzone.csv','w')
	string="well,MD,contribution,type\n"
	file.write(string)
	for well in wells:
		for i in wells[well]['feedzones']:
			x,y,z=MD_to_TVD(well,wells[well]['feedzones'][i]['MD'])
			string="%s,%s,%s,%s\n"%(well,wells[well]['feedzones'][i]['MD'],wells[well]['feedzones'][i]['contribution'],wells[well]['type_w'])
			file.write(string)
	file.close()

def PT_natural_to_GIS(input_dictionary):
	"""It generates a shapefile containing pressure and temperature real data from every well at every layer elevation

	Parameters
	----------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'.

	Returns
	-------
	file
	  layer_{corr}_masl_{masl}.shp: on ../input/PT/GIS/

	Note
	----
	The primary data comes from the defined formation data

	Examples
	--------
	>>> PT_natural_to_GIS(input_dictionary)
	"""

	wells=[]

	for key in ['WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	layers_info=vertical_layers(input_dictionary)

	layer_dict={}
	for v in range(len(layers_info['middle'])):
		layer_dict[layers_info['middle'][v]]=layers_info['name'][v]

	for elevation in layers_info['middle']:
		w=shapefile.Writer('../input/PT/GIS/layer_%s_masl_%s.shp'%(layer_dict[elevation],elevation))
		w.field('TEMPERATURE','F',decimal=2)
		w.field('PRESSURE','F',decimal=2)
		for well in sorted(wells):
			file_source_name="../input/PT/%s_MDPT.dat"%well
			try:
				data=pd.read_csv(file_source_name)
				fun_T=interpolate.interp1d(data['MD'],data['T'])
				fun_P=interpolate.interp1d(data['MD'],data['P'])
				try:
					masl_MD=TVD_to_MD(well,elevation)
					x,y,z=MD_to_TVD(well,masl_MD)
					if not math.isnan(fun_T(masl_MD)) and not math.isnan(fun_P(masl_MD)) and x != np.nan:
						print(x,fun_T(masl_MD))
						w.point(x,y)
						w.record(float(fun_T(masl_MD)),float(fun_P(masl_MD)))
				except (ValueError,shapefile.ShapefileException) :
					pass

			except (IOError,shapefile.ShapefileException):
				pass
		w.close()

def PT_real_to_json(input_dictionary):
	"""It writes a json file based on the formation data (pressure and temperature) at the level of the defined mesh layers.

	Parameters
	----------	  
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'.

	Returns
	-------
	file
	  PT_real_json: en direccion ../input/PT/PT_real_json.txt

	Examples
	--------
	>>> PT_real_to_json(input_dictionary)
	"""

	wells=[]

	for key in ['WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	layers_info=vertical_layers(input_dictionary)

	layer_dict={}
	for v in range(len(layers_info['middle'])):
		layer_dict[layers_info['middle'][v]]=layers_info['name'][v]

	eleme_dict={}

	for well in sorted(wells):
		file_source_name="../input/PT/%s_MDPT.dat"%well
		try:
			data=pd.read_csv(file_source_name)
			fun_T=interpolate.interp1d(data['MD'],data['T'])
			fun_P=interpolate.interp1d(data['MD'],data['P'])
			for masl in layers_info['middle']:
				masl_MD=TVD_to_MD(well,masl)
				try:
					if not np.isnan(masl_MD):
						x,y,z=MD_to_TVD(well,masl_MD)
						eleme_dict["%s-%s"%(well,layer_dict[masl])]=[float(x),float(y),masl,float(fun_T(masl_MD)),float(fun_P(masl_MD))]
				except ValueError:
					pass
		except IOError:
			pass

	with open("../input/PT/PT_real_json.txt",'w') as json_file:
		  json.dump(eleme_dict, json_file,sort_keys=True, indent=1)

def P_from_T_TVD(T_array,TVD_array,water_level_TVD,Pmin):
	"""It generates a pressure log based on real temperature measurements and a hydrostatic level

	Parameters
	----------
	T_array : array
	  Temperature values
	TVD_array : array
	  TVD values associate with every temperature record
	water_level_TVD : float
	  Hydrostatic level on TVD value

	Returns
	-------
	array
	  P: pressure values

	Examples
	--------
	>>> P_from_T_TVD(T_array,TVD_array,water_level_TVD,Pmin)
	"""

	P=[]
	g=formats.formats_t2['PARAMETERS']['GF']
	for n in range(len(TVD_array)):
		if TVD_array[n]<=water_level_TVD:
			if n==0:
				P.append(Pmin)
			else:
				try:
					C0=IAPWS97(T=(T_array[n]+273.15),x=0)
					P.append((water_level_TVD-TVD_array[n])*g*C0.rho/1E5+Pmin)
				except NotImplementedError:
					P.append(P[n-1])
		else:
			P.append(Pmin)
	return P

def survey_to_GIS(input_dictionary):
	"""It writes a shapefile (line type) from the wells surveys

	Parameters
	----------	  
	input_dictionary : dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path'.

	Returns
	-------
	file
	  well_survey: on the path ../mesh/GIS

	Examples
	--------
	>>> survey_to_GIS(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	wells_data=pd.read_sql_query("SELECT * FROM survey ORDER BY well DESC;",conn)
	wells=wells_data.well.unique()

	if len(wells)!=0:
		w=shapefile.Writer('../mesh/GIS/well_survey')
		w.field('WELL', 'C', size=10)
		for well in wells:
			data = wells_data.loc[wells_data['well'] == well]
			points=np.asarray(MD_to_TVD(well,data['MeasuredDepth']))
			points=np.transpose(points)
			w.linez([points.tolist()])
			w.record(well)
		w.close()
	else:
		sys.exit("There is no well survey store on the database")

def feedzone_to_GIS(input_dictionary):
	"""It writes a shapefile (point type) from the wells feedzones position

	Parameters
	----------	  
	input_dictionary : dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path'.

	Returns
	-------
	file
	  well_survey: on the path ../mesh/GIS

	Examples
	--------
	>>> feedzone_to_GIS(input_dictionary)
	"""


	db_path=input_dictionary['db_path']
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	wells_data=pd.read_sql_query("SELECT * FROM wellfeedzone ORDER BY well DESC;",conn)
	wells=wells_data.well.unique()

	wells_info=pd.read_sql_query("SELECT * FROM wells ORDER BY well DESC;",conn)


	if len(wells)!=0:
		w=shapefile.Writer('../mesh/GIS/well_feedzone')
		w.field('WELL', 'C', size=10)
		w.field('TYPE', 'C', size=10)
		w.field('CONTRIBUTION', 'F', decimal=2)
		for i, row in wells_data.iterrows():
			x,y,z=MD_to_TVD(row['well'],row['MeasuredDepth'])
			w.pointz(x,y,z)
			w.record(row['well'],wells_info.loc[wells_info['well']==row['well'],'type'].values[0],row['contribution'])
		w.close()
	else:
		sys.exit("There is no well survey store on the database")