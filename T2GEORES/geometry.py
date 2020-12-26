from model_conf import input_data
from formats import formats_t2
import numpy as np
import csv
from scipy import interpolate
import pandas as pd
import sys
import shapefile
import json
from iapws import IAPWS97

def vertical_layers(input_dictionary=input_data):
	"""Regresa informacion relacionada a las capas

	Returns
	-------
	array
	  Elevacion superior de capa
	array
	  Nombre de capa
	array
	  Elevacion media de capa
	array
	  Elevacion inferior de capa
	
	Examples
	--------
	>>> vertical_layer(layers,z0_level)
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
	"""Retorna las posiciones xyz de una profundidad especifica

	Parameters
	----------
	well : str
	  Pozo seleccionado
	depth : float
	  Profundidad seleccionada para extraccion de informacion


	Returns
	-------
	float
	  x_V : posicion x de profundidad especificada
	float
	  y_V :  posicion y de profundidad especificada
	float
	  z_V :  posicion z de profundidad especificada
	  
	Attention
	---------
	Los archivos input/ubication.csv e input/survey/{pozo}_MD.dat deben existir

	Note
	----
	Se utiliza una regresion lineal entre cada punto del registro

	Examples
	--------
	>>> MD_to_TVD('AH-1',500)
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

def MD_to_TVD_one_var_array(well,var_array,MD_array,num_points):
	"""Encuentra la posicion xyz de cada punto a lo largo de un registro,  junto con la temperatura asociada

	Parameters
	----------
	well : str
	  Pozo seleccionado
	var_array : array
	  Arreglo que contiene registro de valores de Presion o temperatura
	MD_array   :array
	  Arreglo que contiene registro de valores de profundidad medida
	num_points	:int
	  Numero de puntos a interpolar

	Returns
	-------
	array
	  x_V : arreglo con posicion x de cada punto del registro
	array
	  y_V : arreglo con posicion y de cada punto del registro
	array
	  z_V : arreglo con posicion z de cada punto del registro
	array
	  v_V : arreglo con valores de Presion o Temperatura para cada punto xyz
	  
	Attention
	---------
	Los archivos input/ubication.csv e input/survey/{pozo}_MD.dat deben existir

	Note
	----
	Se utiliza una regresion lineal entre cada punto del registro

	Examples
	--------
	>>> MD_to_TVD_one_var_array('AH-16',data['Temp'],data['MD'],100)
	"""

	file="../input/survey/%s_MD.dat"%well
	MD,DeltaY,DeltaX=np.loadtxt(file,skiprows=1,unpack=True,delimiter=',')
	print(well)

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

def TVD_to_MD(well,TVD):
	"""Encuentra la profundidad medida para un vapor de msnm solicitado

	Parameters
	----------
	well : str
	  Pozo seleccionado
	TVD : float
	  msnm de profundidad medida solicitada

	Returns
	-------
	float
	  MD : profundidad medida
	  
	Attention
	---------
	Los archivos input/ubication.csv e input/survey/{pozo}_MD.dat deben existir

	Note
	----
	Se utiliza una regresion lineal entre cada punto del registro

	Examples
	--------
	>>> TVD_to_MD('AH-16',-100)
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
	"""Retorna las profundidades medidas para una serie de valores TVD

	Parameters
	----------
	well : str
	  Pozo seleccionado
	TVD_array : array
	  Arreglo de msnm

	Returns
	-------
	array
	  MD : arreglo de profundidades medidas
	  
	Attention
	---------
	Los archivos input/ubication.csv e input/survey/{pozo}_MD.dat deben existir

	Note
	----
	Se utiliza una regresion lineal entre cada punto del registro

	Examples
	--------
	>>> TVD_to_MD_array('AH-34',data['TVD'])
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

def line_intersect(Ax1, Ay1, Ax2, Ay2, Bx1, By1, Bx2, By2):
	"""Encentra el punto de interseccion de dos lineas

	Parameters
	----------	  
	{letter}{position}{corr} : float
	  Identifica el punto A o B, la posicion ( x o y ) y el correlativo (1 o 2)

	Returns
	-------
	tuple
	  par (x,y), de no encontrar interseccion, returna none
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

#print(MD_to_TVD('AH-1',500))

def write_well_track(input_dictionary=input_data,source_txt='../input/'):
	"""Convierte el survey MD en TVD de todos los pozos

	Parameters
	----------	  
	source_txt : str
	  Ubicacion de archivos fuentes
	wells : array
	  Arreglo de nombre de pozos

	Returns
	-------
	file
	  {pozo}_xyz.csv: en direccion ../input/survey/xyz

	Examples
	--------
	>>> write_well_track(wells)
	"""
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

#write_well_track(['AH-34'])

def write_feedzone_position(source_txt='../input/'):
	"""Genera un archivo con formato json que contiene la presion y temperatura para todos los bloques de un pozo asociados a una posicion en el espacio

	Parameters
	----------	  
	source_txt : str
	  Ubicacion de archivos fuentes

	Returns
	-------
	file
	  well_feezone_xyz: en direccion ../input

	Note
	----
	Este archivo es utilizado por pyamesh para ubicar los pozos

	Examples
	--------
	>>> write_feedzone_position(source_txt='../input/')
	"""

	source_file=source_txt+'well_feedzone.csv'
	try:
		feedzones=pd.read_csv(source_file,delimiter=",")	
	except FileNotFoundError:
		sys.exit("There is no MD file for the well %s"%source_file)

	file=open(source_txt+'well_feedzone_xyz.csv','w')

	string="well,MD,x,y,z,type\n"
	file.write(string)
	for index,row in feedzones.iterrows():
		x,y,z=MD_to_TVD(row['well'],row['MeasuredDepth'])
		string="%s,%s,%s,%s,%s,%s\n"%(row['well'],row['MeasuredDepth'],x,y,z,row['type'])
		file.write(string)
	file.close()

#write_feedzone_position()

def PT_natural_to_GIS():
	"""Genera un archivo shapefile con informacion de presion y temperatura para cada cada pozo segun el registro seleccionado

	Returns
	-------
	file
	  layer_{corr}_masl_{masl}.shp: en direccion ../input/PT/GIS/

	Examples
	--------
	>>> PT_natural_to_GIS()
	"""
	layers_info=vertical_layers()

	layer_dict={}
	for v in range(len(layers_info['middle'])):
		layer_dict[layers_info['middle'][v]]=layers_info['name'][v]

	for elevation in layers_info['middle']:
		w=shapefile.Writer('../input/PT/GIS/layer_%s_masl_%s.shp'%(layer_dict[elevation],elevation))
		w.field('TEMPERATURE','F',decimal=2)
		w.field('PRESSURE','F',decimal=2)
		for well in sorted(input_data['WELLS']):
			file_source_name="../input/PT/%s_MDPT.dat"%well
			try:
				data=pd.read_csv(file_source_name)
				fun_T=interpolate.interp1d(data['MD'],data['T'])
				fun_P=interpolate.interp1d(data['MD'],data['P'])
				try:
					masl_MD=TVD_to_MD(well,elevation)
					x,y,z=MD_to_TVD(well,masl_MD)
					if float(fun_T(masl_MD)) and float(fun_P(masl_MD)):
						w.point(x,y)
						w.record(float(fun_T(masl_MD)),float(fun_P(masl_MD)))
				except (ValueError,shapefile.ShapefileException) :
					pass

			except (IOError,shapefile.ShapefileException):
				pass
		w.close()

def PT_real_to_json():
	"""Genera un archivo con formato json que contiene la presion y temperatura para todos los bloques de un pozo asociados a una posicion en el espacio

	Returns
	-------
	file
	  PT_real_json: en direccion ../input/PT/PT_real_json.txt

	Examples
	--------
	>>> PT_real_to_json()
	"""

	layers_info=vertical_layers()

	layer_dict={}
	for v in range(len(layers_info['middle'])):
		layer_dict[layers_info['middle'][v]]=layers_info['name'][v]

	eleme_dict={}

	for well in sorted(input_data['WELLS']):
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
	"""Genera un perfil de presion basado en un registro de temperatura y un nivel hidroestatico

	Parameters
	----------
	T_array : array
	  Arreglo de temperatura
	TVD_array : array
	  Arreglo de profundidades verticales
	water_level_TVD : float
	  Profundiadad de nivel hidroestatico

	Returns
	-------
	float
	  P: arreglo de presion 

	Examples
	--------
	>>> P_from_Tlogging_TVD(T_array,TVD_array,water_level_TVD,Pmin)
	"""

	P=[]
	g=formats_t2['PARAMETERS']['GF']
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


